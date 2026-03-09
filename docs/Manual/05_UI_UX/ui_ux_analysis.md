# 05. UI/UX 분석

## 🎨 UI/UX 개요

STOM은 **PyQt5 기반의 데스크톱 애플리케이션**으로, 고성능 시스템 트레이딩을 위한 전문적인 사용자 인터페이스를 제공합니다. 실시간 데이터 처리와 다중 시장 모니터링에 최적화된 UI 설계를 특징으로 합니다.

### UI 기술 스택
```
🖥️ GUI 프레임워크
├── PyQt5 (메인 UI 프레임워크)
├── pyqtgraph (고성능 차트 렌더링)
├── matplotlib (정적 차트 및 분석)
└── QAxWidget (ActiveX 컨트롤 통합)

🎨 스타일링
├── 커스텀 CSS 스타일시트
├── 다크 테마 기본 적용
└── 색상 코딩 시스템
```

---

## 🏗️ UI 아키텍처

### 메인 윈도우 구조

#### 1. MainWindow 클래스 (`ui_mainwindow.py`)

**소스**: 예제 코드 (실제: `ui/ui_mainwindow.py`)

```python
class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.init_signals()
        self.init_threads()
        
        # UI 컴포넌트 초기화
        self.init_tables()
        self.init_charts()
        self.init_buttons()
        self.init_status_bar()
```

#### 2. UI 레이아웃 구조
```
MainWindow
├── 상단 메뉴바
│   ├── 파일 메뉴
│   ├── 설정 메뉴
│   └── 도움말 메뉴
├── 좌측 패널 (종목 관리)
│   ├── 관심종목 리스트
│   ├── 조건검색 결과
│   └── 포트폴리오 현황
├── 중앙 패널 (차트 및 데이터)
│   ├── 실시간 차트
│   ├── 호가창
│   └── 체결내역
├── 우측 패널 (거래 및 전략)
│   ├── 주문 입력
│   ├── 전략 설정
│   └── 백테스팅 결과
└── 하단 상태바
    ├── 연결 상태
    ├── 계좌 정보
    └── 시스템 메시지
```

### 멀티 윈도우 시스템

#### 1. 차트 윈도우 (`dialog_chart`)

**소스**: 예제 코드

```python
class ChartDialog(QDialog):
    """독립 차트 윈도우"""
    def __init__(self, parent):
        super().__init__(parent)
        self.chart_widget = pg.PlotWidget()
        self.crosshair = CrossHair(self)
        self.setup_chart_layout()
```

#### 2. 백테스팅 윈도우 (`dialog_backtest`)

**소스**: 예제 코드

```python
class BacktestDialog(QDialog):
    """백테스팅 전용 윈도우"""
    def __init__(self, parent):
        super().__init__(parent)
        self.result_table = QTableWidget()
        self.performance_chart = pg.PlotWidget()
        self.setup_backtest_ui()
```

---

## 📊 차트 시스템

### PyQtGraph 기반 고성능 차트

#### 1. 차트 렌더링 엔진 (`ui_draw_chart.py`)

**소스**: 예제 코드

```python
class DrawChart:
    """차트 그리기 클래스"""
    def __init__(self, ui):
        self.ui = ui
        self.crosshair = CrossHair(self.ui)
    
    def draw_chart(self, data):
        """차트 데이터 렌더링"""
        # 데이터 전처리
        self.ui.ChartClear()
        coin, xticks, arry, buy_index, sell_index = data[1:]
        
        # 차트 타입별 렌더링
        if is_candlestick:
            self.draw_candlestick_chart(arry, xticks)
        else:
            self.draw_line_chart(arry, xticks)
        
        # 기술적 지표 오버레이
        self.draw_technical_indicators(arry, xticks)
        
        # 매매 신호 표시
        self.draw_trading_signals(buy_index, sell_index)
```

#### 2. 캔들스틱 차트 구현

**소스**: 예제 코드

```python
class CandlestickItem(pg.GraphicsObject):
    """커스텀 캔들스틱 아이템"""
    def __init__(self, data, indices, xticks):
        super().__init__()
        self.data = data
        self.indices = indices  # [현재가, 시가, 고가, 저가]
        self.xticks = xticks
        
    def paint(self, painter, option, widget):
        """캔들스틱 렌더링"""
        for i, x in enumerate(self.xticks):
            current = self.data[i, self.indices[0]]
            open_price = self.data[i, self.indices[1]]
            high = self.data[i, self.indices[2]]
            low = self.data[i, self.indices[3]]
            
            # 양봉/음봉 색상 결정
            color = 'red' if current >= open_price else 'blue'
            
            # 캔들 몸체 그리기
            self.draw_candle_body(painter, x, open_price, current, color)
            
            # 꼬리 그리기
            self.draw_candle_tail(painter, x, high, low, color)
```

#### 3. 실시간 차트 업데이트

**소스**: 예제 코드

```python
class RealTimeChart:
    """실시간 차트 업데이트"""
    def __init__(self, chart_widget):
        self.chart = chart_widget
        self.data_buffer = deque(maxlen=1000)
        
    def update_tick_data(self, tick_data):
        """틱 데이터 업데이트"""
        self.data_buffer.append(tick_data)
        
        # 차트 데이터 갱신
        x_data = list(range(len(self.data_buffer)))
        y_data = [tick['price'] for tick in self.data_buffer]
        
        # 실시간 라인 업데이트
        self.chart.plot(x_data, y_data, pen='yellow', clear=True)
        
        # 자동 스크롤
        self.chart.setXRange(max(0, len(x_data) - 100), len(x_data))
```

### 기술적 지표 시각화

#### 1. 이동평균선

**소스**: 예제 코드

```python
def draw_moving_averages(self, data, xticks):
    """이동평균선 그리기"""
    ma_periods = [5, 10, 20, 60, 120]
    colors = [(180, 180, 180), (140, 140, 140), (100, 100, 100), (80, 80, 80), (60, 60, 60)]
    
    for period, color in zip(ma_periods, colors):
        ma_data = self.calculate_moving_average(data, period)
        self.chart.plot(x=xticks, y=ma_data, pen=color, name=f'MA{period}')
```

#### 2. 볼륨 차트

**소스**: 예제 코드

```python
class VolumeBarsItem(pg.GraphicsObject):
    """볼륨 바 차트"""
    def __init__(self, volume_data, xticks):
        super().__init__()
        self.volume_data = volume_data
        self.xticks = xticks
        
    def paint(self, painter, option, widget):
        """볼륨 바 렌더링"""
        max_volume = max(self.volume_data)
        
        for i, (x, volume) in enumerate(zip(self.xticks, self.volume_data)):
            # 볼륨 바 높이 계산
            bar_height = (volume / max_volume) * 100
            
            # 볼륨 바 그리기
            painter.fillRect(x - 0.4, 0, 0.8, bar_height, QColor(100, 100, 100, 128))
```

---

## 📋 테이블 시스템

### 실시간 데이터 테이블

#### 1. 관심종목 테이블

**소스**: 예제 코드

```python
class WatchlistTable(QTableWidget):
    """관심종목 테이블"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_table()
        self.setup_context_menu()
        
    def setup_table(self):
        """테이블 초기 설정"""
        headers = ['종목명', '현재가', '등락률', '거래량', '시가', '고가', '저가']
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 컬럼 너비 자동 조정
        self.horizontalHeader().setStretchLastSection(True)
        
    def update_row_data(self, row, data):
        """행 데이터 업데이트"""
        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            
            # 등락률에 따른 색상 설정
            if col == 2:  # 등락률 컬럼
                if value > 0:
                    item.setForeground(QColor(255, 100, 100))  # 빨간색
                elif value < 0:
                    item.setForeground(QColor(100, 100, 255))  # 파란색
                    
            self.setItem(row, col, item)
```

#### 2. 호가창 테이블

**소스**: 예제 코드

```python
class OrderbookTable(QTableWidget):
    """호가창 테이블"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_orderbook()
        
    def setup_orderbook(self):
        """호가창 초기 설정"""
        self.setRowCount(20)  # 매도 10단계 + 매수 10단계
        self.setColumnCount(3)  # 잔량, 호가, 잔량
        
        headers = ['매도잔량', '호가', '매수잔량']
        self.setHorizontalHeaderLabels(headers)
        
    def update_orderbook(self, orderbook_data):
        """호가 데이터 업데이트"""
        # 매도 호가 (상단)
        for i in range(10):
            sell_qty = orderbook_data.get(f'매도잔량{10-i}', 0)
            sell_price = orderbook_data.get(f'매도호가{10-i}', 0)
            
            self.setItem(i, 0, QTableWidgetItem(f"{sell_qty:,}"))
            self.setItem(i, 1, QTableWidgetItem(f"{sell_price:,}"))
            
            # 매도 호가 배경색 (빨간색 계열)
            self.item(i, 1).setBackground(QColor(100, 50, 50))
            
        # 매수 호가 (하단)
        for i in range(10):
            buy_qty = orderbook_data.get(f'매수잔량{i+1}', 0)
            buy_price = orderbook_data.get(f'매수호가{i+1}', 0)
            
            self.setItem(i+10, 2, QTableWidgetItem(f"{buy_qty:,}"))
            self.setItem(i+10, 1, QTableWidgetItem(f"{buy_price:,}"))
            
            # 매수 호가 배경색 (파란색 계열)
            self.item(i+10, 1).setBackground(QColor(50, 50, 100))
```

### 백테스팅 결과 테이블

#### 1. 거래 내역 테이블

**소스**: 예제 코드

```python
class TradeHistoryTable(QTableWidget):
    """거래 내역 테이블"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_trade_table()
        
    def setup_trade_table(self):
        """거래 테이블 설정"""
        headers = [
            '일시', '종목', '매매구분', '수량', '가격', 
            '수수료', '세금', '실현손익', '누적손익'
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
    def add_trade_record(self, trade_data):
        """거래 기록 추가"""
        row = self.rowCount()
        self.insertRow(row)
        
        for col, value in enumerate(trade_data):
            item = QTableWidgetItem(str(value))
            
            # 매매구분에 따른 색상
            if col == 2:  # 매매구분
                if value == '매수':
                    item.setForeground(QColor(255, 100, 100))
                else:
                    item.setForeground(QColor(100, 100, 255))
                    
            # 손익에 따른 색상
            elif col in [7, 8]:  # 실현손익, 누적손익
                if float(value) > 0:
                    item.setForeground(QColor(255, 100, 100))
                elif float(value) < 0:
                    item.setForeground(QColor(100, 100, 255))
                    
            self.setItem(row, col, item)
```

---

## 🎛️ 컨트롤 패널

### 주문 입력 패널

#### 1. 주문 위젯

**소스**: 예제 코드

```python
class OrderWidget(QWidget):
    """주문 입력 위젯"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_order_ui()
        self.connect_signals()
        
    def setup_order_ui(self):
        """주문 UI 설정"""
        layout = QVBoxLayout()
        
        # 종목 선택
        self.symbol_combo = QComboBox()
        layout.addWidget(QLabel("종목"))
        layout.addWidget(self.symbol_combo)
        
        # 주문 타입
        self.order_type_group = QButtonGroup()
        self.market_order_radio = QRadioButton("시장가")
        self.limit_order_radio = QRadioButton("지정가")
        self.order_type_group.addButton(self.market_order_radio)
        self.order_type_group.addButton(self.limit_order_radio)
        
        layout.addWidget(self.market_order_radio)
        layout.addWidget(self.limit_order_radio)
        
        # 수량 및 가격
        self.quantity_spinbox = QSpinBox()
        self.price_spinbox = QDoubleSpinBox()
        
        layout.addWidget(QLabel("수량"))
        layout.addWidget(self.quantity_spinbox)
        layout.addWidget(QLabel("가격"))
        layout.addWidget(self.price_spinbox)
        
        # 주문 버튼
        self.buy_button = QPushButton("매수")
        self.sell_button = QPushButton("매도")
        
        self.buy_button.setStyleSheet("background-color: red; color: white;")
        self.sell_button.setStyleSheet("background-color: blue; color: white;")
        
        layout.addWidget(self.buy_button)
        layout.addWidget(self.sell_button)
        
        self.setLayout(layout)
```

### 전략 설정 패널

#### 1. 전략 파라미터 위젯

**소스**: 예제 코드

```python
class StrategyWidget(QWidget):
    """전략 설정 위젯"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_strategy_ui()
        
    def setup_strategy_ui(self):
        """전략 UI 설정"""
        layout = QFormLayout()
        
        # 전략 선택
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['이동평균', 'RSI', 'MACD', '볼린저밴드'])
        layout.addRow("전략", self.strategy_combo)
        
        # 파라미터 설정
        self.param1_spinbox = QDoubleSpinBox()
        self.param2_spinbox = QDoubleSpinBox()
        self.param3_spinbox = QDoubleSpinBox()
        
        layout.addRow("파라미터 1", self.param1_spinbox)
        layout.addRow("파라미터 2", self.param2_spinbox)
        layout.addRow("파라미터 3", self.param3_spinbox)
        
        # 리스크 관리
        self.stop_loss_spinbox = QDoubleSpinBox()
        self.take_profit_spinbox = QDoubleSpinBox()
        
        layout.addRow("손절률 (%)", self.stop_loss_spinbox)
        layout.addRow("익절률 (%)", self.take_profit_spinbox)
        
        # 전략 제어 버튼
        self.start_button = QPushButton("전략 시작")
        self.stop_button = QPushButton("전략 중지")
        
        layout.addRow(self.start_button)
        layout.addRow(self.stop_button)
        
        self.setLayout(layout)
```

---

## 🎨 스타일링 시스템

### 다크 테마 구현

#### 1. 스타일시트 정의 (`set_style.py`)

**소스**: 예제 코드

```python
# 색상 정의
color_fg_bt = 'color: white'
color_bg_bt = 'background-color: #2E2E2E'
color_bg_ld = 'background-color: #404040'

# 폰트 정의
qfont12 = QFont()
qfont12.setFamily('맑은 고딕')
qfont12.setPointSize(12)

# 버튼 스타일
button_style = f"""
QPushButton {{
    {color_fg_bt};
    {color_bg_bt};
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px;
}}
QPushButton:hover {{
    background-color: #404040;
}}
QPushButton:pressed {{
    background-color: #1E1E1E;
}}
"""

# 테이블 스타일
table_style = f"""
QTableWidget {{
    {color_fg_bt};
    {color_bg_bt};
    gridline-color: #555555;
    selection-background-color: #404040;
}}
QHeaderView::section {{
    {color_fg_bt};
    background-color: #333333;
    border: 1px solid #555555;
    padding: 4px;
}}
"""
```

#### 2. 동적 색상 시스템

**소스**: 예제 코드

```python
class ColorManager:
    """색상 관리 클래스"""
    
    # 기본 색상 팔레트
    COLORS = {
        'background': '#2E2E2E',
        'foreground': '#FFFFFF',
        'accent': '#404040',
        'border': '#555555',
        'positive': '#FF6464',  # 상승 (빨간색)
        'negative': '#6464FF',  # 하락 (파란색)
        'neutral': '#CCCCCC',   # 중립 (회색)
        'warning': '#FFAA00',   # 경고 (주황색)
        'success': '#00AA00',   # 성공 (녹색)
    }
    
    @classmethod
    def get_price_color(cls, current, previous):
        """가격 변동에 따른 색상 반환"""
        if current > previous:
            return cls.COLORS['positive']
        elif current < previous:
            return cls.COLORS['negative']
        else:
            return cls.COLORS['neutral']
    
    @classmethod
    def get_volume_color(cls, volume, avg_volume):
        """거래량에 따른 색상 반환"""
        if volume > avg_volume * 1.5:
            return cls.COLORS['warning']
        elif volume > avg_volume:
            return cls.COLORS['success']
        else:
            return cls.COLORS['neutral']
```

---

## 🔄 실시간 UI 업데이트

### 멀티스레드 UI 업데이트

#### 1. Writer 스레드 (`ui_mainwindow.py`)

**소스**: 예제 코드

```python
class Writer(QThread):
    """UI 업데이트 전용 스레드"""
    
    # 시그널 정의
    signal_update_table = pyqtSignal(str, list)
    signal_update_chart = pyqtSignal(str, dict)
    signal_update_status = pyqtSignal(str)
    
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.queue = Queue()
        self.running = True
        
    def run(self):
        """스레드 실행"""
        while self.running:
            try:
                data = self.queue.get(timeout=1)
                self.process_update_data(data)
            except Empty:
                continue
                
    def process_update_data(self, data):
        """업데이트 데이터 처리"""
        update_type = data.get('type')
        
        if update_type == 'table':
            self.signal_update_table.emit(data['table_name'], data['row_data'])
        elif update_type == 'chart':
            self.signal_update_chart.emit(data['chart_name'], data['chart_data'])
        elif update_type == 'status':
            self.signal_update_status.emit(data['message'])
```

#### 2. 시그널-슬롯 연결

**소스**: 예제 코드

```python
def connect_signals(self):
    """시그널-슬롯 연결"""
    # Writer 스레드 시그널 연결
    self.writer.signal_update_table.connect(self.update_table_data)
    self.writer.signal_update_chart.connect(self.update_chart_data)
    self.writer.signal_update_status.connect(self.update_status_bar)
    
    # 사용자 입력 시그널 연결
    self.buy_button.clicked.connect(self.on_buy_clicked)
    self.sell_button.clicked.connect(self.on_sell_clicked)
    
    # 테이블 선택 시그널 연결
    self.watchlist_table.itemSelectionChanged.connect(self.on_symbol_selected)

@pyqtSlot(str, list)
def update_table_data(self, table_name, row_data):
    """테이블 데이터 업데이트"""
    if table_name == 'watchlist':
        self.watchlist_table.update_row_data(row_data[0], row_data[1:])
    elif table_name == 'orderbook':
        self.orderbook_table.update_orderbook(row_data)
```

### 성능 최적화

#### 1. 차트 렌더링 최적화

**소스**: 예제 코드

```python
class OptimizedChart:
    """최적화된 차트 클래스"""
    
    def __init__(self, chart_widget):
        self.chart = chart_widget
        self.data_cache = {}
        self.last_update_time = 0
        self.update_interval = 100  # 100ms
        
    def update_chart_data(self, new_data):
        """차트 데이터 업데이트 (최적화)"""
        current_time = time.time() * 1000
        
        # 업데이트 간격 제한
        if current_time - self.last_update_time < self.update_interval:
            return
            
        # 데이터 변경 확인
        data_hash = hash(str(new_data))
        if data_hash == self.data_cache.get('hash'):
            return
            
        # 차트 업데이트
        self.chart.plot(new_data['x'], new_data['y'], clear=True)
        
        # 캐시 업데이트
        self.data_cache['hash'] = data_hash
        self.last_update_time = current_time
```

#### 2. 메모리 관리

**소스**: 예제 코드

```python
class MemoryManager:
    """메모리 관리 클래스"""
    
    def __init__(self, max_data_points=10000):
        self.max_data_points = max_data_points
        self.data_buffers = {}
        
    def add_data_point(self, buffer_name, data_point):
        """데이터 포인트 추가"""
        if buffer_name not in self.data_buffers:
            self.data_buffers[buffer_name] = deque(maxlen=self.max_data_points)
            
        self.data_buffers[buffer_name].append(data_point)
        
    def get_recent_data(self, buffer_name, count=100):
        """최근 데이터 조회"""
        if buffer_name in self.data_buffers:
            return list(self.data_buffers[buffer_name])[-count:]
        return []
        
    def clear_old_data(self):
        """오래된 데이터 정리"""
        for buffer_name in self.data_buffers:
            if len(self.data_buffers[buffer_name]) > self.max_data_points:
                # 절반 정도 데이터 제거
                keep_count = self.max_data_points // 2
                old_data = list(self.data_buffers[buffer_name])
                self.data_buffers[buffer_name] = deque(
                    old_data[-keep_count:], 
                    maxlen=self.max_data_points
                )
```

---

## 🖱️ 사용자 상호작용

### 마우스 및 키보드 이벤트

#### 1. 차트 상호작용

**소스**: 예제 코드

```python
class ChartInteraction:
    """차트 상호작용 처리"""
    
    def __init__(self, chart_widget):
        self.chart = chart_widget
        self.setup_interactions()
        
    def setup_interactions(self):
        """상호작용 설정"""
        # 마우스 이벤트 연결
        self.chart.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.chart.scene().sigMouseClicked.connect(self.on_mouse_clicked)
        
        # 키보드 이벤트 연결
        self.chart.keyPressEvent = self.on_key_pressed
        
    def on_mouse_moved(self, pos):
        """마우스 이동 이벤트"""
        # 십자선 업데이트
        if self.chart.sceneBoundingRect().contains(pos):
            mouse_point = self.chart.plotItem.vb.mapSceneToView(pos)
            self.update_crosshair(mouse_point.x(), mouse_point.y())
            
    def on_mouse_clicked(self, event):
        """마우스 클릭 이벤트"""
        if event.double():
            # 더블클릭 시 차트 리셋
            self.chart.autoRange()
        else:
            # 단일클릭 시 정보 표시
            mouse_point = self.chart.plotItem.vb.mapSceneToView(event.pos())
            self.show_price_info(mouse_point.x(), mouse_point.y())
            
    def on_key_pressed(self, event):
        """키보드 이벤트"""
        if event.key() == Qt.Key_Space:
            # 스페이스바로 일시정지/재개
            self.toggle_real_time_update()
        elif event.key() == Qt.Key_R:
            # R키로 차트 리셋
            self.chart.autoRange()
```

#### 2. 컨텍스트 메뉴

**소스**: 예제 코드

```python
class ContextMenuManager:
    """컨텍스트 메뉴 관리"""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.setup_context_menus()
        
    def setup_context_menus(self):
        """컨텍스트 메뉴 설정"""
        # 테이블 컨텍스트 메뉴
        self.table_menu = QMenu(self.parent)
        self.table_menu.addAction("관심종목 추가", self.add_to_watchlist)
        self.table_menu.addAction("관심종목 제거", self.remove_from_watchlist)
        self.table_menu.addSeparator()
        self.table_menu.addAction("차트 보기", self.show_chart)
        self.table_menu.addAction("상세 정보", self.show_details)
        
        # 차트 컨텍스트 메뉴
        self.chart_menu = QMenu(self.parent)
        self.chart_menu.addAction("확대", self.zoom_in)
        self.chart_menu.addAction("축소", self.zoom_out)
        self.chart_menu.addAction("자동 범위", self.auto_range)
        self.chart_menu.addSeparator()
        self.chart_menu.addAction("이미지 저장", self.save_chart_image)
        
    def show_table_context_menu(self, position):
        """테이블 컨텍스트 메뉴 표시"""
        self.table_menu.exec_(self.parent.mapToGlobal(position))
        
    def show_chart_context_menu(self, position):
        """차트 컨텍스트 메뉴 표시"""
        self.chart_menu.exec_(self.parent.mapToGlobal(position))
```

---

## 📱 반응형 레이아웃

### 동적 레이아웃 관리

#### 1. 스플리터 기반 레이아웃

**소스**: 예제 코드

```python
class ResponsiveLayout:
    """반응형 레이아웃 관리"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_splitters()
        
    def setup_splitters(self):
        """스플리터 설정"""
        # 메인 수평 스플리터
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # 좌측 패널 (종목 리스트)
        self.left_panel = self.create_left_panel()
        
        # 중앙 패널 (차트)
        self.center_panel = self.create_center_panel()
        
        # 우측 패널 (주문/전략)
        self.right_panel = self.create_right_panel()
        
        # 스플리터에 패널 추가
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.center_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # 초기 크기 비율 설정
        self.main_splitter.setSizes([300, 800, 300])
        
    def create_center_panel(self):
        """중앙 패널 생성"""
        center_widget = QWidget()
        layout = QVBoxLayout()
        
        # 상단 차트
        self.chart_splitter = QSplitter(Qt.Vertical)
        self.main_chart = pg.PlotWidget()
        self.volume_chart = pg.PlotWidget()
        
        self.chart_splitter.addWidget(self.main_chart)
        self.chart_splitter.addWidget(self.volume_chart)
        self.chart_splitter.setSizes([700, 200])
        
        layout.addWidget(self.chart_splitter)
        center_widget.setLayout(layout)
        
        return center_widget
```

#### 2. 창 크기 변경 대응

**소스**: 예제 코드

```python
def resizeEvent(self, event):
    """창 크기 변경 이벤트"""
    super().resizeEvent(event)
    
    # 최소 크기 확인
    if self.width() < 1200 or self.height() < 800:
        self.resize(1200, 800)
        
    # 패널 크기 조정
    self.adjust_panel_sizes()
    
def adjust_panel_sizes(self):
    """패널 크기 자동 조정"""
    total_width = self.width()
    
    if total_width < 1400:
        # 작은 화면에서는 우측 패널 숨김
        self.right_panel.hide()
        self.main_splitter.setSizes([300, total_width - 300, 0])
    else:
        # 큰 화면에서는 모든 패널 표시
        self.right_panel.show()
        self.main_splitter.setSizes([300, total_width - 600, 300])
```

---

## 🔧 UI 유틸리티

### 크로스헤어 구현

#### 1. CrossHair 클래스 (`ui_crosshair.py`)

**소스**: 예제 코드

```python
class CrossHair:
    """차트 십자선 구현"""
    
    def __init__(self, ui):
        self.ui = ui
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.label = pg.TextItem()
        
    def setup_crosshair(self, chart_widget):
        """십자선 설정"""
        chart_widget.addItem(self.vLine, ignoreBounds=True)
        chart_widget.addItem(self.hLine, ignoreBounds=True)
        chart_widget.addItem(self.label, ignoreBounds=True)
        
        # 마우스 이동 이벤트 연결
        chart_widget.scene().sigMouseMoved.connect(self.update_crosshair)
        
    def update_crosshair(self, pos):
        """십자선 위치 업데이트"""
        if self.ui.chart_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.ui.chart_widget.plotItem.vb.mapSceneToView(pos)
            
            # 십자선 위치 설정
            self.vLine.setPos(mouse_point.x())
            self.hLine.setPos(mouse_point.y())
            
            # 가격 및 시간 정보 표시
            self.update_price_label(mouse_point.x(), mouse_point.y())
            
    def update_price_label(self, x, y):
        """가격 라벨 업데이트"""
        # 시간 변환
        time_str = self.convert_x_to_time(x)
        
        # 가격 포맷
        price_str = f"{y:,.0f}"
        
        # 라벨 텍스트 설정
        label_text = f"시간: {time_str}\n가격: {price_str}"
        self.label.setText(label_text)
        self.label.setPos(x, y)
```

---

*다음: [06. 데이터 관리](../06_Data/data_management.md)* 