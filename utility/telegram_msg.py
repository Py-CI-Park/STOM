import os
import time
from queue import Empty, Queue
from threading import Event, Thread

import telegram
import pandas as pd

from backtester.analysis.output_config import get_backtesting_output_config
from utility.setting import DICT_SET
from telegram.ext import Updater, MessageHandler, Filters


class TelegramMsg:
    def __init__(self, qlist):
        """
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdzservQ, totalQ
           0        1       2      3       4      5      6      7       8         9         10     11    12      13       14
        """
        self.windowQ  = qlist[0]
        self.teleQ    = qlist[3]
        self.ctraderQ = qlist[9]
        self.cstgQ    = qlist[10]
        self.wdzservQ = qlist[13]
        self.dict_set = DICT_SET
        self.gubun    = self.dict_set['증권사'][4:]
        self.updater  = None
        self.bot      = None
        self.photo_queue = []
        self.last_photo_time = 0.0
        self.photo_send_queue = Queue()
        self.photo_sender_stop = Event()
        self.photo_sender_thread = None
        self._load_output_config()
        self.UpdateBot()
        self._start_photo_sender()
        self.Start()

    def Start(self):
        while True:
            try:
                data = self.teleQ.get(timeout=self.photo_poll_timeout)
            except Empty:
                self.FlushPhotoQueue()
                continue

            if type(data) == str:
                if '.png' in data and os.path.exists(data):
                    self.QueuePhoto(data)
                else:
                    self.FlushPhotoQueue(force=True)
                    self.SendMsg(data)
            elif type(data) == pd.DataFrame:
                self.FlushPhotoQueue(force=True)
                self.UpdateDataframe(data)
            elif isinstance(data, (list, tuple)) and data and data[0] == '설정변경':
                self.FlushPhotoQueue(force=True)
                if self.updater is not None:
                    self.updater.stop()
                    self.updater = None
                self.dict_set = data[1]
                self.gubun = int(self.dict_set['증권사'][4:])
                self.UpdateBot()
                self._load_output_config()
                if self.enable_telegram_async:
                    self._start_photo_sender()
                else:
                    self._stop_photo_sender()

    def __del__(self):
        self._stop_photo_sender()
        if self.updater is not None:
            self.updater.stop()

    def UpdateBot(self):
        if self.updater is None and self.dict_set[f'텔레그램봇토큰{self.gubun}'] is not None:
            try:
                self.bot = telegram.Bot(self.dict_set[f'텔레그램봇토큰{self.gubun}'])
            except:
                print('텔레그램 설정 오류 알림 - 텔레그램 봇토큰이 잘못되어 봇을 만들 수 없습니다.')
            else:
                self.SetCustomButton()
        else:
            self.bot = None

    def SetCustomButton(self):
        custum_button = [
            ['S잔고청산', 'S전략중지', 'C잔고청산', 'C전략중지'],
            ['S체결목록', 'S거래목록', 'S잔고평가'],
            ['C체결목록', 'C거래목록', 'C잔고평가'],
            ['S스톰라이브', 'C스톰라이브', '백테라이브']
        ]
        reply_markup = telegram.ReplyKeyboardMarkup(custum_button)
        self.bot.send_message(chat_id=self.dict_set[f'텔레그램사용자아이디{self.gubun}'], text='사용자버튼 설정을 완료하였습니다.', reply_markup=reply_markup)
        self.updater = Updater(self.dict_set[f'텔레그램봇토큰{self.gubun}'])
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.ButtonClicked))
        self.updater.start_polling(drop_pending_updates=True)

    def ButtonClicked(self, update, context):
        if context == '':
            return
        cmd = update.message.text
        if cmd == 'S전략중지':
            self.wdzservQ.put(('strategy', '매수전략중지'))
            self.SendMsg('주식 전략 중지 완료')
        elif cmd == 'C전략중지':
            self.cstgQ.put('매수전략중지')
            self.SendMsg('코인 전략 중지 완료')
        elif '라이브' in cmd:
            self.windowQ.put(cmd)
        elif 'S' in cmd:
            self.wdzservQ.put(('trader', cmd))
        elif 'C' in cmd:
            self.ctraderQ.put(cmd)

    def SendMsg(self, msg):
        if self.bot is not None:
            try:
                text = '' if msg is None else str(msg)
                # Telegram 메시지 길이 제한(약 4096자) 대응
                max_len = 3500
                if len(text) <= max_len:
                    self.bot.sendMessage(chat_id=self.dict_set[f'텔레그램사용자아이디{self.gubun}'], text=text)
                    return

                for part in self._SplitText(text, max_len=max_len):
                    self.bot.sendMessage(chat_id=self.dict_set[f'텔레그램사용자아이디{self.gubun}'], text=part)
                    time.sleep(0.05)
            except Exception as e:
                print(f'텔레그램 명령 오류 알림 - sendMessage {e}')
        else:
            print('텔레그램 설정 오류 알림 - 텔레그램 봇이 설정되지 않아 메세지를 보낼 수 없습니다.')

    @staticmethod
    def _SplitText(text: str, max_len: int = 3500):
        """
        Telegram 메시지 길이 제한 대응용 분할 유틸.
        - 줄 단위로 최대한 유지하며, 한 줄이 너무 길면 강제 분할합니다.
        """
        if not text:
            return []

        lines = text.splitlines(keepends=True)
        chunks = []
        buf = ''

        for line in lines:
            if len(buf) + len(line) <= max_len:
                buf += line
                continue

            if buf:
                chunks.append(buf)
                buf = ''

            if len(line) <= max_len:
                buf = line
                continue

            # 한 줄이 너무 긴 경우 강제 분할
            for i in range(0, len(line), max_len):
                chunks.append(line[i:i + max_len])

        if buf:
            chunks.append(buf)

        return chunks

    def SendPhoto(self, path):
        if self.bot is not None:
            try:
                with open(path, 'rb') as image:
                    self.bot.send_photo(chat_id=self.dict_set[f'텔레그램사용자아이디{self.gubun}'], photo=image)
            except Exception as e:
                print(f'텔레그램 명령 오류 알림 - send_photo {e}')
        else:
            print('텔레그램 설정 오류 알림 - 텔레그램 봇이 설정되지 않아 스크린샷를 보낼 수 없습니다.')

    def SendMediaGroup(self, paths):
        if not paths:
            return
        if self.bot is None:
            for path in paths:
                self.SendPhoto(path)
            return

        for i in range(0, len(paths), self.photo_batch_max):
            chunk = paths[i:i + self.photo_batch_max]
            if len(chunk) == 1:
                self.SendPhoto(chunk[0])
                continue

            opened_files = []
            try:
                media_group = []
                for path in chunk:
                    f = open(path, 'rb')
                    opened_files.append(f)
                    media_group.append(telegram.InputMediaPhoto(media=f))
                self.bot.send_media_group(
                    chat_id=self.dict_set[f'텔레그램사용자아이디{self.gubun}'],
                    media=media_group
                )
            except Exception as e:
                print(f'텔레그램 명령 오류 알림 - send_media_group {e}')
                for path in chunk:
                    self.SendPhoto(path)
            finally:
                for f in opened_files:
                    try:
                        f.close()
                    except Exception:
                        pass

    def QueuePhoto(self, path):
        if not path:
            return
        self.photo_queue.append(path)
        self.last_photo_time = time.time()
        if len(self.photo_queue) >= self.photo_batch_max:
            self.FlushPhotoQueue(force=True)

    def FlushPhotoQueue(self, force: bool = False):
        if not self.photo_queue:
            return
        if not force and (time.time() - self.last_photo_time) < self.photo_flush_interval:
            return
        paths = self.photo_queue
        self.photo_queue = []
        self.last_photo_time = 0.0
        if self.enable_telegram_async:
            self.photo_send_queue.put(paths)
        else:
            self.SendMediaGroup(paths)

    def _load_output_config(self):
        cfg = get_backtesting_output_config()
        self.enable_telegram_async = bool(cfg.get('enable_telegram_async', False))
        self.photo_batch_max = int(cfg.get('telegram_batch_size', 10))
        self.photo_flush_interval = float(cfg.get('telegram_batch_interval_s', 1.0))
        self.photo_poll_timeout = float(cfg.get('telegram_queue_timeout_s', 0.2))

    def _start_photo_sender(self):
        if not self.enable_telegram_async:
            return
        if self.photo_sender_thread is not None:
            return
        self.photo_sender_thread = Thread(target=self._photo_sender_loop, daemon=True)
        self.photo_sender_thread.start()

    def _stop_photo_sender(self):
        if self.photo_sender_thread is None:
            return
        self.photo_sender_stop.set()
        self.photo_send_queue.put(None)
        try:
            self.photo_sender_thread.join(timeout=1.0)
        except Exception:
            pass
        self.photo_sender_thread = None

    def _photo_sender_loop(self):
        while not self.photo_sender_stop.is_set():
            try:
                batch = self.photo_send_queue.get(timeout=0.5)
            except Empty:
                continue
            if batch is None:
                break
            self.SendMediaGroup(batch)

    def UpdateDataframe(self, df):
        total_rows = len(df)
        max_rows = 200
        prefix = ''
        if total_rows > max_rows:
            df = df.tail(max_rows).copy()
            prefix = f'(최근 {max_rows}건만 표시, 총 {total_rows:,}건)\n'

        if '매수금액' in df.columns:
            text = prefix
            for index in df.index:
                ct    = df['체결시간'][index][8:10] + ':' + df['체결시간'][index][10:12]
                per   = df['수익률'][index]
                sg    = df['수익금'][index]
                name  = df['종목명'][index]
                text += f'{ct} {per:.2f}% {sg:,.0f}원 {name}\n'
            self.SendMsg(text)
        elif '매입가' in df.columns:
            text   = prefix
            m_unit = '원' if df.columns[1] == '매입가' else 'USDT'
            for index in df.index:
                per   = df['수익률'][index]
                sg    = df['평가손익'][index]
                name  = df['종목명'][index]
                if df.columns[1] == '매입가':
                    text += f'{per:.2f}% {sg:,.0f}{m_unit} {name}\n'
                else:
                    pos   = df['포지션'][index]
                    text += f'{pos} {per:.2f}% {sg:,.0f}{m_unit} {name}\n'
            tbg   = df['매입금액'].sum()
            tpg   = df['평가금액'].sum()
            tsg   = df['평가손익'].sum()
            tpp   = round(tsg / tbg * 100, 2)
            text += f'{tbg:,.0f}{m_unit} {tpg:,.0f}{m_unit} {tpp:.2f}% {tsg:,.0f}{m_unit}\n'
            self.SendMsg(text)
        elif '주문구분' in df.columns:
            text = prefix
            for index in df.index:
                ct   = df['체결시간'][index][8:10] + ':' + df['체결시간'][index][10:12]
                bs   = df['주문구분'][index]
                bp   = df['체결가'][index]
                name = df['종목명'][index]
                text += f'{ct} {bs} {bp:,.0f} {name}\n'
            self.SendMsg(text)
