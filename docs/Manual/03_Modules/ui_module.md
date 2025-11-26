# UI 모듈 (ui/)

## 📋 개요

UI 모듈은 **PyQt5** 기반의 전문 트레이딩 인터페이스로, 실시간 차트, 거래 내역, 잔고 관리, 전략 설정 등 모든 트레이딩 기능을 시각화합니다. 멀티스레드 아키텍처를 통해 논블로킹 UI 반응성을 보장합니다.

---

## 🏗 모듈 구조

```
ui/
├── ui_mainwindow.py              # 메인 윈도우 및 Writer 스레드
│
├── ui_button_clicked_*.py        # 버튼 이벤트 핸들러 (다수)
│   ├── ui_button_clicked_sd.py   # 주식/코인 설정 탭
│   ├── ui_button_clicked_svj.py  # 주식 변수 관리
│   ├── ui_button_clicked_svjs.py # 주식 변수 상세
│   ├── ui_button_clicked_svjb.py # 주식 변수 백테스트
│   ├── ui_button_clicked_svoa.py # 주식 최적화
│   ├── ui_button_clicked_cvj.py  # 코인 변수 관리
│   ├── ui_button_clicked_cvjs.py # 코인 변수 상세
│   ├── ui_button_clicked_cvjb.py # 코인 변수 백테스트
│   ├── ui_button_clicked_cvoa.py # 코인 최적화
│   ├── ui_button_clicked_chart.py # 차트 버튼
│   ├── ui_button_clicked_etc.py  # 기타 버튼
│   └── ... (약 20개 파일)
│
├── ui_update_*.py                # UI 업데이트 핸들러
│   ├── ui_update_tablewidget.py  # 테이블 위젯 업데이트
│   ├── ui_update_textedit.py     # 텍스트 편집 업데이트
│   └── ui_update_progressbar.py  # 프로그레스바 업데이트
│
├── ui_draw_*.py                  # 차트 그리기
│   ├── ui_draw_chart.py          # 일반 차트 (matplotlib)
│   ├── ui_draw_realchart.py      # 실시간 차트 (pyqtgraph)
│   ├── ui_draw_jisuchart.py      # 지수 차트
│   └── ui_draw_treemap.py        # 트리맵 (히트맵)
│
├── set_*.py                      # UI 컴포넌트 설정
│   ├── set_style.py              # 스타일 시트
│   ├── set_icon.py               # 아이콘 설정
│   ├── set_table.py              # 테이블 설정
│   ├── set_widget.py             # 위젯 생성
│   ├── set_mainmenu.py           # 메인 메뉴
│   ├── set_logtap.py             # 로그 탭
│   ├── set_ordertap.py           # 주문 탭
│   ├── set_setuptap.py           # 설정 탭
│   ├── set_sbtap.py              # 주식 백테스트 탭
│   ├── set_cbtap.py              # 코인 백테스트 탭
│   ├── set_dialog_back.py        # 백테스트 다이얼로그
│   ├── set_dialog_chart.py       # 차트 다이얼로그
│   └── set_dialog_etc.py         # 기타 다이얼로그
│
└── ui_*.py                       # 기타 UI 핸들러
    ├── ui_activated_*.py         # 활성화 이벤트
    ├── ui_cell_clicked.py        # 셀 클릭 이벤트
    ├── ui_text_changed.py        # 텍스트 변경 이벤트
    ├── ui_process_*.py           # 프로세스 관리
    ├── ui_backtest_engine.py     # 백테스트 엔진 연동
    └── ... (약 30개 추가 파일)
```

**참고**:
- `dialog/` 서브폴더는 없으며, 다이얼로그 관련 파일은 `set_dialog_*.py` 형식입니다
- 버튼 이벤트 핸들러가 기능별로 세분화되어 20개 이상의 파일로 구성됩니다
- 실제로는 총 **67개의 Python 파일**이 ui/ 폴더에 있습니다

---

## 🖥 메인 윈도우 (ui_mainwindow.py)

### MainWindow 클래스

#### 1. 초기화 및 큐 시스템

**소스**: `ui/ui_mainwindow.py:413-1083`

```python
class MainWindow(QMainWindow):
    """메인 윈도우"""
    def __init__(self, auto_run_):
        super().__init__()

        # 자동 실행 모드
        self.auto_run = auto_run_
        self.dict_set = DICT_SET

        # 15개 전용 큐 초기화
        self.qlist = [Queue() for _ in range(15)]
        '''
        qlist[0]  = windowQ     # UI 업데이트
        qlist[1]  = soundQ      # 알림 소리
        qlist[2]  = queryQ      # DB 쿼리
        qlist[3]  = teleQ       # 텔레그램
        qlist[4]  = chartQ      # 차트 데이터
        qlist[5]  = hogaQ       # 호가 데이터
        qlist[6]  = webcQ       # 웹 크롤링
        qlist[7]  = backQ       # 백테스팅
        qlist[8]  = sreceivQ    # 주식 수신
        qlist[9]  = straderQ    # 주식 거래
        qlist[10] = sstgQ       # 주식 전략
        qlist[11] = creceivQ    # 코인 수신
        qlist[12] = ctraderQ    # 코인 거래
        qlist[13] = cstgQ       # 코인 전략
        qlist[14] = totalQ      # 통합 데이터
        '''

        # ZeroMQ 통신 설정
        self.zmqserver = ZmqServ(self.qlist[13], 5555)
        self.zmqclient = ZmqRecv(self.qlist, 5777)

        # Writer 스레드 (UI 업데이트 전용)
        self.writer = Writer(self.qlist[0])
        self.writer.signal1.connect(self.UpdateTexedit)
        self.writer.signal2.connect(self.UpdateTablewidget)
        self.writer.signal3.connect(self.UpdateChart)
        self.writer.signal4.connect(self.UpdateHoga)
        self.writer.signal5.connect(self.UpdateProgressbar)
        self.writer.signal6.connect(self.UpdateTreemap)
        self.writer.signal7.connect(self.UpdateIndexChart)
        self.writer.signal8.connect(self.UpdateRealChart)
        self.writer.signal9.connect(self.UpdateStatusbar)
        self.writer.start()

        # UI 설정
        self.SetWindow()
        self.SetTabs()
```

#### 2. 프로세스 관리

**소스**: `ui/ui_process_starter.py` (프로세스 시작 로직)

```python
def StartProcesses(self):
    """프로세스 시작"""
    # 주식 프로세스
    if self.dict_set['주식리시버']:
        self.proc_receiver_stock = Process(
            target=StockReceiverTick,
            args=(self.qlist,),
            daemon=True
        )
        self.proc_receiver_stock.start()

    if self.dict_set['주식트레이더']:
        self.proc_trader_stock = Process(
            target=StockTrader,
            args=(self.qlist,),
            daemon=True
        )
        self.proc_trader_stock.start()

    if self.dict_set['주식전략']:
        self.proc_strategy_stock = Process(
            target=StockStrategyTick,
            args=(self.qlist,),
            daemon=True
        )
        self.proc_strategy_stock.start()

    # 코인 프로세스
    if self.dict_set['코인리시버']:
        self.proc_receiver_coin = Process(
            target=CoinReceiverTick,
            args=(self.qlist,),
            daemon=True
        )
        self.proc_receiver_coin.start()

    # 백테스트 프로세스
    if self.dict_set['백테스터']:
        self.proc_backtester = Process(
            target=Backtester,
            args=(self.qlist,),
            daemon=True
        )
        self.proc_backtester.start()
```

### Writer 스레드

#### 1. pyqtSignal 정의

**소스**: `ui/ui_mainwindow.py:282-411`

```python
class Writer(QThread):
    """UI 업데이트 전용 스레드"""
    signal1 = pyqtSignal(tuple)  # 텍스트 업데이트
    signal2 = pyqtSignal(tuple)  # 테이블 업데이트
    signal3 = pyqtSignal(tuple)  # 차트 업데이트
    signal4 = pyqtSignal(tuple)  # 호가 업데이트
    signal5 = pyqtSignal(tuple)  # 프로그레스바 업데이트
    signal6 = pyqtSignal(tuple)  # 트리맵 업데이트
    signal7 = pyqtSignal(tuple)  # 지수차트 업데이트
    signal8 = pyqtSignal(tuple)  # 실시간차트 업데이트
    signal9 = pyqtSignal(str)    # 상태바 업데이트

    def __init__(self, windowQ):
        super().__init__()
        self.windowQ = windowQ

    def run(self):
        """큐에서 메시지 수신 및 신호 발송"""
        while True:
            try:
                data = self.windowQ.get()

                if data[0] == 'text':
                    self.signal1.emit(data)
                elif data[0] == 'table':
                    self.signal2.emit(data)
                elif data[0] == 'chart':
                    self.signal3.emit(data)
                elif data[0] == 'hoga':
                    self.signal4.emit(data)
                elif data[0] == 'progress':
                    self.signal5.emit(data)
                elif data[0] == 'treemap':
                    self.signal6.emit(data)
                elif data[0] == 'index':
                    self.signal7.emit(data)
                elif data[0] == 'realchart':
                    self.signal8.emit(data)
                elif data[0] == 'statusbar':
                    self.signal9.emit(data[1])

            except Exception as e:
                print(f"Writer 스레드 에러: {e}")
```

---

## 📊 차트 시스템

### 1. 정적 차트 (ui_draw_chart.py)

#### matplotlib 기반 캔들스틱 차트

**소스**: `ui/ui_draw_chart.py`

```python
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import mplfinance as mpf

class ChartWidget(FigureCanvas):
    """차트 위젯"""
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(12, 6))
        super().__init__(self.fig)
        self.setParent(parent)

        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False

    def DrawCandleChart(self, df, title=''):
        """캔들스틱 차트 그리기"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # mplfinance 스타일 설정
        mc = mpf.make_marketcolors(
            up='r', down='b',
            edge='inherit',
            wick={'up':'r', 'down':'b'},
            volume='in',
            alpha=0.8
        )
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)

        # 차트 그리기
        mpf.plot(
            df,
            type='candle',
            style=s,
            volume=True,
            ax=ax,
            title=title
        )

        self.draw()

    def DrawLineChart(self, df, columns, title=''):
        """라인 차트 그리기"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        for col in columns:
            ax.plot(df.index, df[col], label=col)

        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle=':')

        self.draw()
```

#### 기술적 지표 오버레이

**소스**: 예제 코드 (`ui/ui_draw_chart.py` 참조)

```python
def DrawChartWithIndicators(self, df):
    """기술적 지표가 포함된 차트"""
    self.fig.clear()

    # 서브플롯 생성
    ax1 = self.fig.add_subplot(3, 1, 1)  # 가격 차트
    ax2 = self.fig.add_subplot(3, 1, 2)  # RSI
    ax3 = self.fig.add_subplot(3, 1, 3)  # MACD

    # 캔들스틱 차트
    mpf.plot(df, type='candle', ax=ax1, volume=False)

    # 이동평균선 추가
    ax1.plot(df.index, df['MA5'], label='MA5', color='orange')
    ax1.plot(df.index, df['MA20'], label='MA20', color='green')
    ax1.legend()

    # RSI
    ax2.plot(df.index, df['RSI'], label='RSI', color='purple')
    ax2.axhline(y=70, color='r', linestyle='--')
    ax2.axhline(y=30, color='b', linestyle='--')
    ax2.legend()

    # MACD
    ax3.plot(df.index, df['MACD'], label='MACD', color='blue')
    ax3.plot(df.index, df['Signal'], label='Signal', color='red')
    ax3.bar(df.index, df['Histogram'], label='Histogram', alpha=0.3)
    ax3.legend()

    self.draw()
```

### 2. 실시간 차트 (ui_draw_realchart.py)

#### pyqtgraph 기반 실시간 차트

**소스**: `ui/ui_draw_realchart.py`

```python
import pyqtgraph as pg
from pyqtgraph import PlotWidget

class RealChartWidget(PlotWidget):
    """실시간 차트 위젯"""
    def __init__(self, parent=None):
        super().__init__(parent)

        # 차트 설정
        self.setBackground('k')
        self.showGrid(x=True, y=True, alpha=0.3)

        # 데이터 버퍼
        self.max_data_points = 1000
        self.x_data = []
        self.y_data = []

        # 라인 플롯
        self.plot_line = self.plot(pen=pg.mkPen('y', width=2))

    def UpdateRealChart(self, timestamp, price):
        """실시간 차트 업데이트"""
        # 데이터 추가
        self.x_data.append(timestamp)
        self.y_data.append(price)

        # 버퍼 크기 제한
        if len(self.x_data) > self.max_data_points:
            self.x_data = self.x_data[-self.max_data_points:]
            self.y_data = self.y_data[-self.max_data_points:]

        # 차트 업데이트
        self.plot_line.setData(self.x_data, self.y_data)

    def DrawCandlestickRealtime(self, candles):
        """실시간 캔들스틱"""
        self.clear()

        # 캔들 데이터 생성
        candle_item = pg.CandlestickItem()

        for i, candle in enumerate(candles):
            candle_item.addCandle(
                time=i,
                open=candle['open'],
                high=candle['high'],
                low=candle['low'],
                close=candle['close']
            )

        self.addItem(candle_item)
```

---

## 📋 테이블 업데이트 (ui_update_tablewidget.py)

### 거래 내역 테이블

**소스**: `ui/ui_update_tablewidget.py`

```python
class TableUpdater:
    """테이블 업데이트 관리"""

    @staticmethod
    def UpdateTradeTable(table_widget, trade_data):
        """거래 내역 테이블 업데이트"""
        row = table_widget.rowCount()
        table_widget.insertRow(row)

        # 데이터 삽입
        table_widget.setItem(row, 0, QTableWidgetItem(trade_data['시간']))
        table_widget.setItem(row, 1, QTableWidgetItem(trade_data['종목명']))
        table_widget.setItem(row, 2, QTableWidgetItem(trade_data['주문구분']))
        table_widget.setItem(row, 3, QTableWidgetItem(str(trade_data['수량'])))
        table_widget.setItem(row, 4, QTableWidgetItem(str(trade_data['가격'])))
        table_widget.setItem(row, 5, QTableWidgetItem(str(trade_data['체결금액'])))

        # 색상 설정
        if trade_data['주문구분'] == '매수':
            table_widget.item(row, 2).setForeground(QColor(255, 0, 0))
        else:
            table_widget.item(row, 2).setForeground(QColor(0, 0, 255))

    @staticmethod
    def UpdateBalanceTable(table_widget, balance_data):
        """잔고 테이블 업데이트"""
        table_widget.clearContents()
        table_widget.setRowCount(len(balance_data))

        for i, (code, data) in enumerate(balance_data.items()):
            table_widget.setItem(i, 0, QTableWidgetItem(data['종목명']))
            table_widget.setItem(i, 1, QTableWidgetItem(str(data['보유수량'])))
            table_widget.setItem(i, 2, QTableWidgetItem(str(data['매입가'])))
            table_widget.setItem(i, 3, QTableWidgetItem(str(data['현재가'])))
            table_widget.setItem(i, 4, QTableWidgetItem(str(data['평가손익'])))
            table_widget.setItem(i, 5, QTableWidgetItem(f"{data['수익률']:.2f}%"))

            # 수익률에 따른 색상
            if data['수익률'] > 0:
                table_widget.item(i, 5).setForeground(QColor(255, 0, 0))
            else:
                table_widget.item(i, 5).setForeground(QColor(0, 0, 255))
```

---

## 🎨 스타일 설정 (set_style.py)

### QSS 스타일시트

**소스**: `ui/set_style.py`

```python
class StyleSheet:
    """스타일시트 관리"""

    @staticmethod
    def GetDarkTheme():
        """다크 테마"""
        return """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }

        QTableWidget {
            background-color: #2d2d2d;
            alternate-background-color: #3d3d3d;
            color: #ffffff;
            gridline-color: #555555;
        }

        QPushButton {
            background-color: #0d47a1;
            color: #ffffff;
            border: none;
            padding: 5px;
            border-radius: 3px;
        }

        QPushButton:hover {
            background-color: #1565c0;
        }

        QPushButton:pressed {
            background-color: #0a3d91;
        }

        QLineEdit {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 3px;
        }

        QTextEdit {
            background-color: #2d2d2d;
            color: #00ff00;
            border: 1px solid #555555;
        }
        """
```

---

## 🔔 이벤트 핸들러

### 버튼 클릭 이벤트 (ui_button_clicked_s1.py)

**소스**: `ui/ui_button_clicked_*.py` 파일들 (각 탭별 이벤트 핸들러)

```python
class StockTabEventHandler:
    """주식 탭 이벤트 핸들러"""

    def ButtonClicked_StartTrading(self):
        """거래 시작 버튼"""
        # 설정 검증
        if not self.ValidateSettings():
            QMessageBox.warning(self, '경고', '설정을 확인해주세요.')
            return

        # 프로세스 시작
        self.StartTradingProcesses()

        # UI 업데이트
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.statusbar.showMessage('거래 시작됨')

    def ButtonClicked_StopTrading(self):
        """거래 중지 버튼"""
        # 프로세스 종료
        self.StopTradingProcesses()

        # UI 업데이트
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.statusbar.showMessage('거래 중지됨')

    def ButtonClicked_LoadStrategy(self):
        """전략 불러오기 버튼"""
        # 전략 다이얼로그 열기
        dialog = StrategyDialog(self)
        if dialog.exec_():
            strategy = dialog.GetSelectedStrategy()
            self.LoadStrategy(strategy)
```

---

## 📱 다이얼로그

### 전략 설정 다이얼로그 (dialog_strategy.py)

**소스**: 예제 코드 (`ui/set_dialog_*.py` 파일들 참조)

```python
class StrategyDialog(QDialog):
    """전략 설정 다이얼로그"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('전략 설정')
        self.setModal(True)

        # 레이아웃
        layout = QVBoxLayout()

        # 전략 선택
        self.combo_strategy = QComboBox()
        self.combo_strategy.addItems(['이동평균', 'RSI', 'MACD', '볼린저밴드'])
        layout.addWidget(QLabel('전략 선택:'))
        layout.addWidget(self.combo_strategy)

        # 파라미터 입력
        self.spin_param1 = QSpinBox()
        self.spin_param2 = QSpinBox()
        layout.addWidget(QLabel('파라미터 1:'))
        layout.addWidget(self.spin_param1)
        layout.addWidget(QLabel('파라미터 2:'))
        layout.addWidget(self.spin_param2)

        # 버튼
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton('확인')
        btn_cancel = QPushButton('취소')
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
```

---

## 🚀 성능 최적화

### 1. 논블로킹 UI

**소스**: 예제 코드 (UI 업데이트 패턴)

```python
def UpdateUI(self, data):
    """UI 업데이트 (논블로킹)"""
    # Worker 스레드에서 처리
    QTimer.singleShot(0, lambda: self._update_ui_internal(data))

def _update_ui_internal(self, data):
    """내부 UI 업데이트 로직"""
    # 실제 UI 업데이트 수행
    pass
```

### 2. 배치 업데이트

**소스**: 예제 코드 (테이블 업데이트 최적화 패턴)

```python
def BatchUpdateTable(self, data_list):
    """테이블 배치 업데이트"""
    # 테이블 업데이트 중지
    self.table.setUpdatesEnabled(False)

    # 모든 데이터 업데이트
    for data in data_list:
        self.UpdateRow(data)

    # 테이블 업데이트 재개
    self.table.setUpdatesEnabled(True)
```

---

*다음: [유틸리티 모듈](utility_module.md)*
*이전: [암호화폐 모듈](coin_module.md)*
