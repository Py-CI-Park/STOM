# PyTrader 매도 조건식 및 변수 정리

## 문서 목적
1. **PyTrader에서 사용되는 매도 조건식과 변수 정리**
2. **STOM 문법에 맞게 매도 로직을 재구성하여 STOM 프로그램에 적용**
3. **LLM(GPT) 활용 시 이해하기 쉽고, 질문하기 용이하도록 명확히 정리**



## 매도 조건 정리

### 매도시점 1 [Sell Stage 1]
1. **Protection Percent 조건**:
   - 손실률이 `protection_percent` 이상이면 매도.
   - 손익률이 `protection_percent` 이하이고, `protection_percent`가 음수인 경우 매도.
   - 손실률이 `|protection_percent|` 이상이며, `protection_percent`가 음수인 경우 매도.

### 매도시점 2 [Sell Stage 2]
1. **High Protection Percent 조건**:
   - 매수가 대비 최고가 상승폭이 `high_protection_percent` 이상인 경우.
   - 이후 최고가 대비 현재가 하락폭이 `high_protection_percent` 이상이면 매도.

### 매도시점 3 [Sell Stage 3]
1. **Target Percent 조건**:
   - 목표 수익률 도달 시 매도. (2.75%)
   - 목표 수익률 도달 후 상승세가 아니고, 최고가에서 `second_high_protection_percent` 이상 하락 시 매도. (0.5 %)

### 매도시점 4 [Sell Stage 4]
1. **목표 수익 후 고가 하락 조건**:
   - 목표 수익 도달 후, 고가 대비 일정 비율 하락 시 매도.

### 매도시점 5 [Sell Stage 5]
1. **목표 수익 이후 수익률 하락 조건**:
   - 목표 수익 도달 후, 수익률이 `(target_percent - target_percent_damper)` 이하로 하락 시 매도.

### 매도시점 6 [Sell Stage 6]
1. **Second/Third Target 조건**:
   - 2차 목표 수익률 2.25% 도달 후, 1.5% 수익률 발생 시 매도.
   - 3차 목표 수익률 1.75% 도달 후, 1.0% 수익률 하락 시 매도.

### 매도시점 7 [Sell Stage 7]
1. **Partial Sell 조건**:
   - 1차 부분 매도: 수익률이 `first_partial_sell_target_percent` 이상 도달 시 실행. (2.0 %)
   - 2차 부분 매도: 남은 주식의 일부를 설정된 비율로 매도. (2.5 %)

### 매도시점 8 [Sell Stage 8]
1. **보유 시간 조건**:
   - 설정된 최대 보유 시간을 초과하면 매도. (90s 이상 보유 시 매도)

### 매도시점 10 [Sell Stage 10]
1. **상한가 도달 조건**:
   - 현재가가 전일 종가 대비 29% 이상 상승 시 매도.

### 매도시점 11~13 [Sell Stage 11~13]
1. **수익/손실 종료 조건**:
   - 전체 수익금이 목표 수익금 대비 설정된 배수 도달 시 매도.
   - 목표 배수 도달 후 일정 비율 하락 시 매도.
   - 전체 손실금이 설정된 손실 한도 초과 시 매도.

### 매도시점 21 [Sell Stage 21]
1. **목표 종목 수익 도달 조건**:
   - 설정된 목표 수익 종목 개수 도달 시 매도.


## 매도 조건식에 사용된 변수 정리

### 1. 시스템 전역 변수
- **`self.protection_percent`**:
  - 매도 조건 1에서 사용.
  - 손실 허용 한도를 비율로 설정.

- **`self.high_protection_percent`**:
  - 매도 조건 2에서 사용.
  - 최고가 대비 허용 하락률.

- **`self.target_percent`**:
  - 매도 조건 3, 5에서 사용.
  - 목표 수익률 설정.

- **`self.second_high_protection_percent`**:
  - 매도 조건 3, 4에서 사용.
  - 목표 수익 후 허용 하락률.

- **`self.target_percent_damper`**:
  - 매도 조건 5에서 사용.
  - 목표 수익 이후 허용 수익 하락 완화 비율.

- **`self.time_limitation`**:
  - 매도 조건 8에서 사용.
  - 보유 시간 제한 여부 설정.

- **`self.keeping_time_second`**:
  - 매도 조건 8에서 사용.
  - 보유 시간 제한 설정 (초 단위).

- **`self.partial_sell`**:
  - 매도 조건 7에서 사용.
  - 부분 매도 여부 설정.

- **`self.first_partial_sell_target_percent`**:
  - 매도 조건 7-1에서 사용.
  - 1차 부분 매도 조건의 목표 수익률.

- **`self.first_partial_sell_ratio`**:
  - 매도 조건 7-1에서 사용.
  - 1차 부분 매도 비율.

- **`self.second_partial_sell_target_percent`**:
  - 매도 조건 7-2에서 사용.
  - 2차 부분 매도 조건의 목표 수익률.

- **`self.second_partial_sell_ratio`**:
  - 매도 조건 7-2에서 사용.
  - 2차 부분 매도 비율.

- **`self.profit_check`**:
  - 매도 조건 11, 12, 13에서 사용.
  - 전체 수익금/손실금 확인 조건.

- **`self.win_lose_check`**:
  - 매도 조건 21에서 사용.
  - 목표 종목 수익 조건 확인 여부.

---

### 2. 종목별 변수 (`stock_data`)
- **`buy`**:
  - 매수가.
  
- **`current`**:
  - 현재가.

- **`high`**:
  - 최고가.

- **`earning_rate`**:
  - 현재 수익률 (%) 계산 값.

- **`elapsed_time`**:
  - 보유 시간 (초 단위).

- **`before_price`**:
  - 직전 종가.

- **`sell_stage`**:
  - 현재 종목의 매도 단계 상태를 기록.

- **`order_status`**:
  - 매도 주문 상태.

- **`left_stock_number`**:
  - 남은 주식 수량.

- **`first_partial_sell_stock_number`**:
  - 1차 부분 매도 주식 수.

- **`second_partial_sell_stock_number`**:
  - 2차 부분 매도 주식 수.

- **`first_partial_profit`**:
  - 1차 부분 매도로 발생한 수익금.

- **`profit`**:
  - 현재 종목의 총 수익금.

- **`target_status`**:
  - 목표 수익 도달 여부 (`목표수익도달` 또는 `목표수익미도달`).

---

### 3. 시간 계산 변수
- **`current_time`**:
  - 현재 시간.

- **`keeping_time`**:
  - 보유 시간 계산 (현재 시간 - 매수 시간).

- **`check_time`**:
  - 조건 만족 시점의 시간.

- **`last_send_order_time`**:
  - 마지막 매도 주문 시간.

---

### 4. 기타
- **`sell_type`**:
  - 매도 주문 유형 (예: 시장가, 지정가).

- **`sell_damper_2`**:
  - 매도 주문 감쇠 비율.

- **`commission_rate`**:
  - 수수료 비율.

- **`tax_rate`**:
  - 세금 비율.



---

## STOM 가이드라인 기반 Python 코드 (누락 포함)

```python
class SellConditionManager:
    def __init__(self, config):
        """
        Initialize the sell condition manager.

        Args:
            config (dict): Configuration parameters for all sell conditions.
        """
        self.config = config

    def check_sell_conditions(self, stock_data):
        """
        Evaluate stock sell conditions based on STOM guidelines.

        Args:
            stock_data (dict): Dictionary containing stock details like buy price, current price, high, etc.

        Returns:
            list: List of triggered sell stages.
        """
        triggered_stages = []
        buy_price = stock_data['buy']
        current_price = stock_data['current']
        high_price = stock_data['high']
        elapsed_time = stock_data['elapsed_time']
        earning_rate = stock_data['earning_rate']

        # Sell Stage 1
        loss_percent = ((buy_price - current_price) / buy_price) * 100
        if loss_percent >= self.config['protection_percent']:
            triggered_stages.append('Sell Stage 1')

        # Sell Stage 2
        if high_price > buy_price * (1 + self.config['high_protection_percent'] / 100):
            drop_from_high = ((high_price - current_price) / high_price) * 100
            if drop_from_high >= self.config['high_protection_percent']:
                triggered_stages.append('Sell Stage 2')

        # Sell Stage 3
        if earning_rate >= self.config['target_percent']:
            drop_from_high = ((high_price - current_price) / high_price) * 100
            if drop_from_high >= self.config['second_high_protection_percent']:
                triggered_stages.append('Sell Stage 3')

        # Sell Stage 4
        if self.config['target_status'] == '목표수익도달':
            drop_from_high = ((high_price - current_price) / high_price) * 100
            if drop_from_high >= self.config['second_high_protection_percent']:
                triggered_stages.append('Sell Stage 4')

        # Sell Stage 5
        if earning_rate < (self.config['target_percent'] - self.config['target_percent_damper']):
            triggered_stages.append('Sell Stage 5')

        # Sell Stage 8 (Time Limitation)
        if self.config['time_limitation'] and elapsed_time >= self.config['keeping_time_second']:
            triggered_stages.append('Sell Stage 8')

        # Sell Stage 10
        price_change = ((current_price - stock_data['before_price']) / stock_data['before_price']) * 100
        if price_change > 29.0:
            triggered_stages.append('Sell Stage 10')

        # Additional Sell Stages (11~13, 21)
        if self.config.get('profit_check') == '수익 종료 1':
            triggered_stages.append('Sell Stage 11')
        if self.config.get('profit_check') == '수익 종료 2':
            triggered_stages.append('Sell Stage 12')
        if self.config.get('profit_check') == '손실 종료':
            triggered_stages.append('Sell Stage 13')
        if self.config.get('win_lose_check') == '수익 종료':
            triggered_stages.append('Sell Stage 21')

        return triggered_stages


# Example Configuration
config = {
    'protection_percent': 5.0,
    'high_protection_percent': 10.0,
    'target_percent': 15.0,
    'second_high_protection_percent': 5.0,
    'target_percent_damper': 2.0,
    'time_limitation': True,
    'keeping_time_second': 3600,
    'profit_check': None,
    'win_lose_check': None,
}

# Example Stock Data
stock_data = {
    'buy': 100,
    'current': 90,
    'high': 110,
    'elapsed_time': 4000,
    'earning_rate': 12.0,
    'before_price': 70,
}

sell_manager = SellConditionManager(config)
triggered_stages = sell_manager.check_sell_conditions(stock_data)
if triggered_stages:
    print(f"Triggered Sell Stages: {', '.join(triggered_stages)}")
else:
    print("No sell condition met.")
```
