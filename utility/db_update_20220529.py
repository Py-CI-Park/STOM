import os
import sys
import sqlite3
import pandas as pd
from multiprocessing import Process
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from utility.setting import DB_PATH


def GetHogaunit(price):
    if price < 1000:
        x = 1
    elif price < 5000:
        x = 5
    elif price < 10000:
        x = 10
    elif price < 50000:
        x = 50
    else:
        x = 100
    return x


def Updater(gubun, file_list_):
    print(f'[{gubun}] VI호가단위 및 호가정보 업데이트 시작')
    last = len(file_list_)
    for k, db_name in enumerate(file_list_):
        con = sqlite3.connect(f'{DB_PATH}/{db_name}')
        cur = con.cursor()
        df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        table_list = df['name'].to_list()
        for code in table_list:
            if code != 'moneytop':
                df = pd.read_sql(f'SELECT * FROM "{code}"', con).set_index('index')
                df['VI호가단위'] = df['VI가격']
                df['VI호가단위'] = df['VI호가단위'].apply(lambda x: GetHogaunit(x))
                df = df[(df['매수잔량5'] != 0) & (df['매도잔량5'] != 0)]
                df.to_sql(code, con, if_exists='replace', chunksize=1000)
        for code in table_list:
            if code != 'moneytop':
                set_text = '매도호가1 = 매도호가4, 매도호가2 = 매도호가5, 매도호가3 = 0, 매도호가4 = 0, 매도호가5 = 0, ' \
                           '매도잔량1 = 매도잔량4, 매도잔량2 = 매도잔량5, 매도잔량3 = 0, 매도잔량4 = 0, 매도잔량5 = 0'
                cur.execute(f'UPDATE "{code}" SET {set_text} WHERE 매도호가3 < 현재가')
                set_text = '매도호가1 = 매도호가3, 매도호가2 = 매도호가4, 매도호가3 = 매도호가5, 매도호가4 = 0, 매도호가5 = 0, ' \
                           '매도잔량1 = 매도잔량3, 매도잔량2 = 매도잔량4, 매도잔량3 = 매도잔량5, 매도잔량4 = 0, 매도잔량5 = 0'
                cur.execute(f'UPDATE "{code}" SET {set_text} WHERE 매도호가2 < 현재가')
                set_text = '매도호가1 = 매도호가2, 매도호가2 = 매도호가3, 매도호가3 = 매도호가4, 매도호가4 = 매도호가5, 매도호가5 = 0, ' \
                           '매도잔량1 = 매도잔량2, 매도잔량2 = 매도잔량3, 매도잔량3 = 매도잔량4, 매도잔량4 = 매도잔량5, 매도잔량5 = 0'
                cur.execute(f'UPDATE "{code}" SET {set_text} WHERE 매도호가1 < 현재가')
                set_text = '매수호가1 = 매수호가4, 매수호가2 = 매수호가5, 매수호가3 = 0, 매수호가4 = 0, 매수호가5 = 0, ' \
                           '매수잔량1 = 매수잔량4, 매수잔량2 = 매수잔량5, 매수잔량3 = 0, 매수잔량4 = 0, 매수잔량5 = 0'
                cur.execute(f'UPDATE "{code}" SET {set_text} WHERE 매수호가3 > 현재가')
                set_text = '매수호가1 = 매수호가3, 매수호가2 = 매수호가4, 매수호가3 = 매수호가5, 매수호가4 = 0, 매수호가5 = 0, ' \
                           '매수잔량1 = 매수잔량3, 매수잔량2 = 매수잔량4, 매수잔량3 = 매수잔량5, 매수잔량4 = 0, 매수잔량5 = 0'
                cur.execute(f'UPDATE "{code}" SET {set_text} WHERE 매수호가2 > 현재가')
                set_text = '매수호가1 = 매수호가2, 매수호가2 = 매수호가3, 매수호가3 = 매수호가4, 매수호가4 = 매수호가5, 매수호가5 = 0, ' \
                           '매수잔량1 = 매수잔량2, 매수잔량2 = 매수잔량3, 매수잔량3 = 매수잔량4, 매수잔량4 = 매수잔량5, 매수잔량5 = 0'
                cur.execute(f'UPDATE "{code}" SET {set_text} WHERE 매수호가1 > 현재가')
        con.commit()
        cur.execute('VACUUM;')
        con.close()
        print(f'[{gubun}] {db_name} VI호가단위 및 호가정보 업데이트 중 ... [{k + 1}/{last}]')
    print(f'[{gubun}] VI호가단위 및 호가정보 업데이트 완료')


if __name__ == '__main__':
    file_list = os.listdir(DB_PATH)
    file_list = [x for x in file_list if 'stock_tick_' in x and 'back' not in x and '.zip' not in x]

    file_lists = []
    for i in range(4):
        file_lists.append([file for j, file in enumerate(file_list) if j % 4 == i])

    proc_list = []
    for i, file_list in enumerate(file_lists):
        p = Process(target=Updater, args=(i + 1, file_list), daemon=True)
        p.start()
        proc_list.append(p)

    for p in proc_list:
        p.join()
