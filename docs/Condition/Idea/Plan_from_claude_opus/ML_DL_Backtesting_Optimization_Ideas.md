# 머신러닝/딥러닝 기반 백테스팅 조건식 최적화 아이디어

## 1. 개요

### 1.1 현재 상황 분석

현재 STOM 시스템의 백테스팅 조건식 최적화는 다음과 같은 문제점을 가지고 있습니다:

- **수동 최적화의 한계**: 하나씩 조건식을 수정하면서 테스트하는 방식은 시간이 많이 소요되고 비효율적
- **변수 조합의 복잡성**: 54개의 데이터베이스 컬럼과 수많은 파생 변수들의 조합은 천문학적 경우의 수 생성
- **최적점 탐색의 어려움**: Grid Search나 GA 알고리즘으로는 고차원 공간에서 최적점을 찾기 어려움
- **과적합 위험**: 특정 기간의 데이터에 과도하게 최적화되어 실전에서 성능 저하 가능성

### 1.2 머신러닝/딥러닝 접근의 장점

- **자동 특성 추출**: 딥러닝 모델이 자동으로 중요한 패턴과 특성을 학습
- **비선형 관계 학습**: 복잡한 비선형 관계를 효과적으로 모델링
- **병렬 처리**: GPU를 활용한 대규모 병렬 처리로 학습 시간 단축
- **일반화 능력**: 다양한 시장 상황에 대한 일반화된 전략 학습 가능

## 2. 데이터 준비 및 전처리 전략

### 2.1 특성 엔지니어링 (Feature Engineering)

#### 2.1.1 기본 특성 (Raw Features)
```python
# 데이터베이스의 54개 컬럼 직접 활용
basic_features = [
    '현재가', '시가', '고가', '저가', '등락율', 
    '당일거래대금', '체결강도', '거래대금증감', 
    '전일비', '회전율', '전일동시간비', '시가총액',
    '초당매수수량', '초당매도수량', '초당거래대금',
    '매도총잔량', '매수총잔량', '매도호가1-5', '매수호가1-5',
    '매도잔량1-5', '매수잔량1-5', '매도수5호가잔량합'
]
```

#### 2.1.2 파생 특성 (Derived Features)
```python
# 시계열 특성 (Time-series Features)
def create_time_series_features(df, window_sizes=[5, 10, 20, 30, 60]):
    features = {}
    for window in window_sizes:
        # 이동평균
        features[f'ma_{window}'] = df['현재가'].rolling(window).mean()
        # 표준편차
        features[f'std_{window}'] = df['현재가'].rolling(window).std()
        # 모멘텀
        features[f'momentum_{window}'] = df['현재가'].diff(window)
        # RSI
        features[f'rsi_{window}'] = calculate_rsi(df['현재가'], window)
        # 볼린저 밴드
        features[f'bb_upper_{window}'], features[f'bb_lower_{window}'] = calculate_bollinger_bands(df, window)
    return features

# 호가창 불균형 지표
def calculate_order_book_imbalance(df):
    bid_volume = df[['매수잔량1', '매수잔량2', '매수잔량3', '매수잔량4', '매수잔량5']].sum(axis=1)
    ask_volume = df[['매도잔량1', '매도잔량2', '매도잔량3', '매도잔량4', '매도잔량5']].sum(axis=1)
    return (bid_volume - ask_volume) / (bid_volume + ask_volume + 1e-10)

# 거래 강도 지표
def calculate_trading_intensity(df):
    return df['초당거래대금'] / df['초당거래대금'].rolling(30).mean()
```

#### 2.1.3 정규화 및 스케일링
```python
from sklearn.preprocessing import StandardScaler, RobustScaler
import numpy as np

class FeaturePreprocessor:
    def __init__(self):
        self.price_scaler = RobustScaler()  # 이상치에 강건한 스케일러
        self.volume_scaler = StandardScaler()
        self.rate_scaler = StandardScaler()
        
    def fit_transform(self, df):
        # 가격 관련 변수 정규화
        price_cols = ['현재가', '시가', '고가', '저가', '매도호가1-5', '매수호가1-5']
        df[price_cols] = self.price_scaler.fit_transform(df[price_cols])
        
        # 거래량 관련 변수 로그 변환 후 정규화
        volume_cols = ['당일거래대금', '초당매수수량', '초당매도수량', '초당거래대금']
        df[volume_cols] = np.log1p(df[volume_cols])  # 로그 변환
        df[volume_cols] = self.volume_scaler.fit_transform(df[volume_cols])
        
        # 비율 관련 변수 정규화
        rate_cols = ['등락율', '전일비', '회전율', '체결강도']
        df[rate_cols] = self.rate_scaler.fit_transform(df[rate_cols])
        
        return df
```

### 2.2 레이블 생성 (Label Generation)

#### 2.2.1 수익률 기반 레이블
```python
def create_profit_based_labels(df, holding_periods=[1, 5, 10, 30, 60]):
    """
    다양한 보유 기간에 대한 수익률 계산
    """
    labels = {}
    for period in holding_periods:
        # 미래 수익률 계산
        future_return = (df['현재가'].shift(-period) / df['현재가'] - 1) * 100
        
        # 다중 클래스 레이블 (손실, 보합, 소폭상승, 대폭상승)
        labels[f'label_{period}'] = pd.cut(
            future_return, 
            bins=[-np.inf, -2, 0, 2, 5, np.inf],
            labels=['strong_sell', 'sell', 'hold', 'buy', 'strong_buy']
        )
        
        # 이진 레이블 (매수/매도)
        labels[f'binary_{period}'] = (future_return > 1).astype(int)
        
        # 회귀 타겟 (실제 수익률)
        labels[f'return_{period}'] = future_return
        
    return labels
```

#### 2.2.2 최적 진입/청산 시점 레이블
```python
def create_optimal_trading_points(df, window=60):
    """
    지역 최저점(매수)과 최고점(매도) 식별
    """
    # 지역 최저점 찾기 (매수 시점)
    local_min = df['현재가'].rolling(window=window, center=True).min()
    buy_points = (df['현재가'] == local_min).astype(int)
    
    # 지역 최고점 찾기 (매도 시점)
    local_max = df['현재가'].rolling(window=window, center=True).max()
    sell_points = (df['현재가'] == local_max).astype(int)
    
    return buy_points, sell_points
```

## 3. 머신러닝 모델 아키텍처

### 3.1 LightGBM 기반 앙상블 모델

```python
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import precision_score, recall_score, f1_score
import optuna  # 하이퍼파라미터 최적화

class LightGBMTradingModel:
    def __init__(self):
        self.buy_model = None
        self.sell_model = None
        self.feature_importance = {}
        
    def optimize_hyperparameters(self, X, y, n_trials=100):
        """
        Optuna를 사용한 베이지안 최적화
        """
        def objective(trial):
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': trial.suggest_int('num_leaves', 20, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
                'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
                'bagging_freq': trial.suggest_int('bagging_freq', 1, 7),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
                'lambda_l1': trial.suggest_float('lambda_l1', 0, 10),
                'lambda_l2': trial.suggest_float('lambda_l2', 0, 10),
            }
            
            # 시계열 교차 검증
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                train_data = lgb.Dataset(X_train, label=y_train)
                val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
                
                model = lgb.train(
                    params,
                    train_data,
                    valid_sets=[val_data],
                    num_boost_round=1000,
                    callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)]
                )
                
                predictions = model.predict(X_val)
                score = f1_score(y_val, (predictions > 0.5).astype(int))
                scores.append(score)
            
            return np.mean(scores)
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials)
        
        return study.best_params
    
    def train(self, X_train, y_buy, y_sell):
        """
        매수/매도 모델 각각 학습
        """
        # 매수 모델 학습
        buy_params = self.optimize_hyperparameters(X_train, y_buy)
        self.buy_model = lgb.LGBMClassifier(**buy_params)
        self.buy_model.fit(X_train, y_buy)
        
        # 매도 모델 학습
        sell_params = self.optimize_hyperparameters(X_train, y_sell)
        self.sell_model = lgb.LGBMClassifier(**sell_params)
        self.sell_model.fit(X_train, y_sell)
        
        # 특성 중요도 저장
        self.feature_importance['buy'] = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.buy_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.feature_importance['sell'] = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.sell_model.feature_importances_
        }).sort_values('importance', ascending=False)
    
    def predict(self, X):
        """
        매수/매도 신호 예측
        """
        buy_proba = self.buy_model.predict_proba(X)[:, 1]
        sell_proba = self.sell_model.predict_proba(X)[:, 1]
        
        return {
            'buy_signal': buy_proba,
            'sell_signal': sell_proba,
            'buy_decision': (buy_proba > 0.6).astype(int),  # 임계값 조정 가능
            'sell_decision': (sell_proba > 0.6).astype(int)
        }
```

### 3.2 XGBoost 기반 다중 시간대 모델

```python
import xgboost as xgb

class MultiTimeframeXGBoostModel:
    def __init__(self, timeframes=[1, 5, 15, 30, 60]):
        """
        다중 시간대 모델 - 틱, 1분, 5분, 15분, 30분, 60분
        """
        self.timeframes = timeframes
        self.models = {}
        
    def prepare_multiframe_features(self, tick_data):
        """
        틱 데이터를 다양한 시간대로 리샘플링
        """
        features_dict = {}
        
        for tf in self.timeframes:
            if tf == 1:  # 틱 데이터
                resampled = tick_data.copy()
            else:  # 분 데이터
                resampled = tick_data.resample(f'{tf}T').agg({
                    '현재가': 'last',
                    '시가': 'first',
                    '고가': 'max',
                    '저가': 'min',
                    '거래대금': 'sum',
                    '체결강도': 'mean',
                    '매수잔량1': 'last',
                    '매도잔량1': 'last'
                })
            
            # 각 시간대별 특성 생성
            features_dict[f'tf_{tf}'] = create_time_series_features(resampled)
            
        # 모든 시간대 특성 결합
        combined_features = pd.concat(features_dict.values(), axis=1)
        return combined_features
    
    def train_ensemble(self, X, y):
        """
        각 시간대별 모델 학습 후 앙상블
        """
        for tf in self.timeframes:
            # 시간대별 특성 선택
            tf_features = [col for col in X.columns if f'tf_{tf}' in col]
            X_tf = X[tf_features]
            
            # XGBoost 모델 학습
            dtrain = xgb.DMatrix(X_tf, label=y)
            params = {
                'objective': 'binary:logistic',
                'eval_metric': 'auc',
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'tree_method': 'gpu_hist',  # GPU 가속
                'gpu_id': 0
            }
            
            self.models[tf] = xgb.train(
                params, 
                dtrain, 
                num_boost_round=500,
                early_stopping_rounds=50,
                evals=[(dtrain, 'train')],
                verbose_eval=False
            )
    
    def predict_ensemble(self, X):
        """
        앙상블 예측 (가중 평균)
        """
        predictions = []
        weights = [1, 2, 3, 2, 1]  # 중간 시간대에 더 높은 가중치
        
        for tf, weight in zip(self.timeframes, weights):
            tf_features = [col for col in X.columns if f'tf_{tf}' in col]
            X_tf = X[tf_features]
            dtest = xgb.DMatrix(X_tf)
            pred = self.models[tf].predict(dtest)
            predictions.append(pred * weight)
        
        # 가중 평균
        final_prediction = np.sum(predictions, axis=0) / np.sum(weights)
        return final_prediction
```

## 4. 딥러닝 모델 아키텍처

### 4.1 LSTM 기반 시계열 예측 모델

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

class LSTMTradingModel(nn.Module):
    def __init__(self, input_dim, hidden_dim=256, num_layers=3, dropout=0.2):
        super(LSTMTradingModel, self).__init__()
        
        # Multi-layer LSTM
        self.lstm = nn.LSTM(
            input_dim, 
            hidden_dim, 
            num_layers, 
            batch_first=True,
            dropout=dropout,
            bidirectional=True  # 양방향 LSTM
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            hidden_dim * 2,  # bidirectional
            num_heads=8,
            dropout=dropout
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_dim * 2, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 32)
        
        # Output layers
        self.buy_output = nn.Linear(32, 1)
        self.sell_output = nn.Linear(32, 1)
        
        # Activation and regularization
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.batch_norm1 = nn.BatchNorm1d(128)
        self.batch_norm2 = nn.BatchNorm1d(64)
        
    def forward(self, x):
        # LSTM layers
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Global average pooling
        pooled = torch.mean(attn_out, dim=1)
        
        # Fully connected layers
        x = self.fc1(pooled)
        x = self.batch_norm1(x)
        x = self.relu(x)
        x = self.dropout(x)
        
        x = self.fc2(x)
        x = self.batch_norm2(x)
        x = self.relu(x)
        x = self.dropout(x)
        
        x = self.fc3(x)
        x = self.relu(x)
        
        # Output
        buy_signal = torch.sigmoid(self.buy_output(x))
        sell_signal = torch.sigmoid(self.sell_output(x))
        
        return buy_signal, sell_signal

class LSTMTrainer:
    def __init__(self, model, device='cuda'):
        self.model = model.to(device)
        self.device = device
        self.optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=100)
        self.buy_criterion = nn.BCELoss()
        self.sell_criterion = nn.BCELoss()
        
    def prepare_sequences(self, data, seq_length=60):
        """
        시계열 데이터를 LSTM 입력용 시퀀스로 변환
        """
        sequences = []
        buy_labels = []
        sell_labels = []
        
        for i in range(len(data) - seq_length):
            seq = data[i:i+seq_length]
            sequences.append(seq)
            buy_labels.append(data.iloc[i+seq_length]['buy_label'])
            sell_labels.append(data.iloc[i+seq_length]['sell_label'])
        
        return np.array(sequences), np.array(buy_labels), np.array(sell_labels)
    
    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0
        
        for batch_x, batch_buy_y, batch_sell_y in dataloader:
            batch_x = batch_x.to(self.device)
            batch_buy_y = batch_buy_y.to(self.device)
            batch_sell_y = batch_sell_y.to(self.device)
            
            self.optimizer.zero_grad()
            
            buy_pred, sell_pred = self.model(batch_x)
            
            buy_loss = self.buy_criterion(buy_pred.squeeze(), batch_buy_y)
            sell_loss = self.sell_criterion(sell_pred.squeeze(), batch_sell_y)
            
            loss = buy_loss + sell_loss
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            total_loss += loss.item()
        
        return total_loss / len(dataloader)
    
    def evaluate(self, dataloader):
        self.model.eval()
        buy_predictions = []
        sell_predictions = []
        
        with torch.no_grad():
            for batch_x, _, _ in dataloader:
                batch_x = batch_x.to(self.device)
                buy_pred, sell_pred = self.model(batch_x)
                buy_predictions.extend(buy_pred.cpu().numpy())
                sell_predictions.extend(sell_pred.cpu().numpy())
        
        return np.array(buy_predictions), np.array(sell_predictions)
```

### 4.2 Transformer 기반 모델

```python
class TransformerTradingModel(nn.Module):
    def __init__(self, input_dim, d_model=512, nhead=8, num_layers=6, dropout=0.1):
        super(TransformerTradingModel, self).__init__()
        
        # Input embedding
        self.input_embedding = nn.Linear(input_dim, d_model)
        
        # Positional encoding
        self.positional_encoding = PositionalEncoding(d_model, dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=2048,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output layers
        self.fc1 = nn.Linear(d_model, 256)
        self.fc2 = nn.Linear(256, 128)
        
        self.buy_head = nn.Linear(128, 1)
        self.sell_head = nn.Linear(128, 1)
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # Input embedding
        x = self.input_embedding(x)
        x = self.positional_encoding(x)
        
        # Transformer encoding
        x = self.transformer(x)
        
        # Global pooling
        x = x.mean(dim=1)
        
        # Classification heads
        x = self.dropout(torch.relu(self.fc1(x)))
        x = self.dropout(torch.relu(self.fc2(x)))
        
        buy_signal = torch.sigmoid(self.buy_head(x))
        sell_signal = torch.sigmoid(self.sell_head(x))
        
        return buy_signal, sell_signal

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)
```

### 4.3 CNN-LSTM 하이브리드 모델

```python
class CNNLSTMModel(nn.Module):
    def __init__(self, input_channels, seq_length, num_features):
        super(CNNLSTMModel, self).__init__()
        
        # 1D CNN for feature extraction
        self.conv1 = nn.Conv1d(input_channels, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv1d(128, 256, kernel_size=3, padding=1)
        
        self.batch_norm1 = nn.BatchNorm1d(64)
        self.batch_norm2 = nn.BatchNorm1d(128)
        self.batch_norm3 = nn.BatchNorm1d(256)
        
        self.pool = nn.MaxPool1d(2)
        self.dropout = nn.Dropout(0.2)
        
        # LSTM for sequential processing
        lstm_input_size = 256 * (seq_length // 8)  # After 3 pooling layers
        self.lstm = nn.LSTM(lstm_input_size, 128, 2, batch_first=True, bidirectional=True)
        
        # Fully connected layers
        self.fc1 = nn.Linear(256, 128)
        self.fc2 = nn.Linear(128, 64)
        
        # Output layers
        self.buy_output = nn.Linear(64, 1)
        self.sell_output = nn.Linear(64, 1)
        
    def forward(self, x):
        # CNN feature extraction
        batch_size = x.size(0)
        
        # Reshape for CNN (batch, channels, sequence)
        x = x.transpose(1, 2)
        
        x = torch.relu(self.batch_norm1(self.conv1(x)))
        x = self.pool(x)
        x = self.dropout(x)
        
        x = torch.relu(self.batch_norm2(self.conv2(x)))
        x = self.pool(x)
        x = self.dropout(x)
        
        x = torch.relu(self.batch_norm3(self.conv3(x)))
        x = self.pool(x)
        x = self.dropout(x)
        
        # Reshape for LSTM
        x = x.view(batch_size, 1, -1)
        
        # LSTM processing
        lstm_out, _ = self.lstm(x)
        x = lstm_out[:, -1, :]  # Take last time step
        
        # Fully connected layers
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        
        # Output
        buy_signal = torch.sigmoid(self.buy_output(x))
        sell_signal = torch.sigmoid(self.sell_output(x))
        
        return buy_signal, sell_signal
```

## 5. GPU 최적화 전략

### 5.1 PyTorch GPU 활용

```python
import torch
from torch.cuda.amp import autocast, GradScaler

class GPUOptimizedTrainer:
    def __init__(self, model, device='cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.model = model.to(self.device)
        
        # Mixed precision training
        self.scaler = GradScaler()
        
        # Multi-GPU support
        if torch.cuda.device_count() > 1:
            self.model = nn.DataParallel(self.model)
        
        # Optimize for specific GPU architecture
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
    def train_with_amp(self, dataloader, optimizer):
        """
        Automatic Mixed Precision (AMP) 학습
        """
        self.model.train()
        
        for batch_x, batch_y in dataloader:
            batch_x = batch_x.to(self.device)
            batch_y = batch_y.to(self.device)
            
            optimizer.zero_grad()
            
            # Mixed precision forward pass
            with autocast():
                outputs = self.model(batch_x)
                loss = self.criterion(outputs, batch_y)
            
            # Scaled backward pass
            self.scaler.scale(loss).backward()
            self.scaler.step(optimizer)
            self.scaler.update()
    
    def optimize_batch_size(self, sample_data):
        """
        GPU 메모리에 맞는 최적 배치 사이즈 찾기
        """
        batch_size = 32
        max_batch_size = 32
        
        while batch_size <= 2048:
            try:
                # Test forward pass
                test_batch = sample_data[:batch_size].to(self.device)
                _ = self.model(test_batch)
                
                max_batch_size = batch_size
                batch_size *= 2
                
                # Clear cache
                torch.cuda.empty_cache()
                
            except RuntimeError as e:
                if "out of memory" in str(e):
                    break
                else:
                    raise e
        
        return max_batch_size
```

### 5.2 CuPy를 활용한 데이터 전처리 가속

```python
import cupy as cp
import numpy as np

class GPUDataPreprocessor:
    def __init__(self):
        self.gpu_available = cp.cuda.is_available()
        
    def calculate_technical_indicators_gpu(self, data):
        """
        GPU에서 기술적 지표 계산
        """
        if not self.gpu_available:
            return self.calculate_technical_indicators_cpu(data)
        
        # Convert to GPU array
        gpu_data = cp.asarray(data)
        
        # Moving averages on GPU
        ma_5 = self._moving_average_gpu(gpu_data, 5)
        ma_20 = self._moving_average_gpu(gpu_data, 20)
        ma_60 = self._moving_average_gpu(gpu_data, 60)
        
        # RSI on GPU
        rsi = self._rsi_gpu(gpu_data, 14)
        
        # Bollinger Bands on GPU
        bb_upper, bb_lower = self._bollinger_bands_gpu(gpu_data, 20)
        
        # Convert back to CPU
        results = {
            'ma_5': cp.asnumpy(ma_5),
            'ma_20': cp.asnumpy(ma_20),
            'ma_60': cp.asnumpy(ma_60),
            'rsi': cp.asnumpy(rsi),
            'bb_upper': cp.asnumpy(bb_upper),
            'bb_lower': cp.asnumpy(bb_lower)
        }
        
        return results
    
    def _moving_average_gpu(self, data, window):
        """
        GPU에서 이동평균 계산
        """
        kernel = cp.ones(window) / window
        return cp.convolve(data, kernel, mode='valid')
    
    def _rsi_gpu(self, data, period):
        """
        GPU에서 RSI 계산
        """
        deltas = cp.diff(data)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down
        rsi = cp.zeros_like(data)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        for i in range(period, len(data)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi
```

### 5.3 RAPIDS cuDF를 활용한 대용량 데이터 처리

```python
import cudf
import cuml
from cuml.ensemble import RandomForestClassifier as cuRF

class RAPIDSMLPipeline:
    def __init__(self):
        self.preprocessor = None
        self.model = None
        
    def load_and_preprocess_gpu(self, file_path):
        """
        GPU에서 직접 데이터 로드 및 전처리
        """
        # GPU DataFrame으로 직접 로드
        gdf = cudf.read_csv(file_path)
        
        # GPU에서 전처리
        gdf['returns'] = gdf['현재가'].pct_change()
        gdf['log_volume'] = cudf.log1p(gdf['거래대금'])
        
        # Feature engineering on GPU
        for window in [5, 10, 20, 60]:
            gdf[f'ma_{window}'] = gdf['현재가'].rolling(window).mean()
            gdf[f'std_{window}'] = gdf['현재가'].rolling(window).std()
        
        return gdf
    
    def train_gpu_ml_model(self, X_train, y_train):
        """
        RAPIDS cuML을 사용한 GPU 머신러닝
        """
        # Random Forest on GPU
        self.model = cuRF(
            n_estimators=100,
            max_depth=10,
            max_features='sqrt',
            n_streams=4  # GPU streams for parallel execution
        )
        
        self.model.fit(X_train, y_train)
        
        return self.model
    
    def batch_predict_gpu(self, X_test, batch_size=10000):
        """
        대용량 데이터 배치 예측
        """
        predictions = []
        
        for i in range(0, len(X_test), batch_size):
            batch = X_test[i:i+batch_size]
            pred = self.model.predict(batch)
            predictions.append(pred)
        
        return cudf.concat(predictions)
```

## 6. 강화학습 기반 접근

### 6.1 Deep Q-Network (DQN) 트레이딩 에이전트

```python
import gym
from gym import spaces
import random
from collections import deque

class TradingEnvironment(gym.Env):
    def __init__(self, data, initial_balance=10000000):
        super(TradingEnvironment, self).__init__()
        
        self.data = data
        self.initial_balance = initial_balance
        
        # Action space: 0=Hold, 1=Buy, 2=Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: price data + technical indicators + account info
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(100,),  # Number of features
            dtype=np.float32
        )
        
        self.reset()
    
    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares_held = 0
        self.total_profit = 0
        self.trades = []
        
        return self._get_observation()
    
    def step(self, action):
        current_price = self.data.iloc[self.current_step]['현재가']
        
        # Execute action
        if action == 1:  # Buy
            shares_to_buy = min(self.balance // current_price, 100)  # Max 100 shares
            if shares_to_buy > 0:
                self.balance -= shares_to_buy * current_price * 1.00015  # Commission
                self.shares_held += shares_to_buy
                self.trades.append(('buy', current_price, shares_to_buy))
                
        elif action == 2:  # Sell
            if self.shares_held > 0:
                self.balance += self.shares_held * current_price * 0.99985  # Commission
                self.trades.append(('sell', current_price, self.shares_held))
                self.shares_held = 0
        
        # Calculate reward
        self.current_step += 1
        
        portfolio_value = self.balance + self.shares_held * current_price
        reward = (portfolio_value - self.initial_balance) / self.initial_balance
        
        # Check if episode is done
        done = self.current_step >= len(self.data) - 1
        
        return self._get_observation(), reward, done, {}
    
    def _get_observation(self):
        # Current market data
        row = self.data.iloc[self.current_step]
        
        # Technical indicators
        obs = np.array([
            row['현재가'], row['시가'], row['고가'], row['저가'],
            row['등락율'], row['체결강도'], row['거래대금'],
            row['전일비'], row['회전율'],
            # Account info
            self.balance / self.initial_balance,
            self.shares_held,
            # Add more features as needed
        ])
        
        return obs

class DQNAgent:
    def __init__(self, state_size, action_size, learning_rate=0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = learning_rate
        
        # Neural network
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
        
    def _build_model(self):
        model = nn.Sequential(
            nn.Linear(self.state_size, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, self.action_size)
        )
        return model
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        if np.random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.model(state_tensor)
            return np.argmax(q_values.cpu().numpy())
    
    def replay(self, batch_size=32):
        if len(self.memory) < batch_size:
            return
        
        batch = random.sample(self.memory, batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.FloatTensor([e[4] for e in batch])
        
        current_q_values = self.model(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.target_model(next_states).max(1)[0].detach()
        target_q_values = rewards + (1 - dones) * 0.95 * next_q_values
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def update_target_model(self):
        self.target_model.load_state_dict(self.model.state_dict())
```

### 6.2 Proximal Policy Optimization (PPO) 에이전트

```python
class PPOAgent:
    def __init__(self, state_dim, action_dim, lr=3e-4):
        self.actor = self._build_actor(state_dim, action_dim)
        self.critic = self._build_critic(state_dim)
        
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr)
        
        self.clip_param = 0.2
        self.value_loss_coef = 0.5
        self.entropy_coef = 0.01
        
    def _build_actor(self, state_dim, action_dim):
        return nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.Tanh(),
            nn.Linear(256, 128),
            nn.Tanh(),
            nn.Linear(128, action_dim),
            nn.Softmax(dim=-1)
        )
    
    def _build_critic(self, state_dim):
        return nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.Tanh(),
            nn.Linear(256, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )
    
    def get_action(self, state):
        state = torch.FloatTensor(state).unsqueeze(0)
        probs = self.actor(state)
        dist = torch.distributions.Categorical(probs)
        action = dist.sample()
        return action.item(), dist.log_prob(action)
    
    def update(self, states, actions, rewards, log_probs, next_states, dones):
        # Convert to tensors
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        old_log_probs = torch.FloatTensor(log_probs)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        # Calculate advantages
        values = self.critic(states).squeeze()
        next_values = self.critic(next_states).squeeze()
        
        deltas = rewards + 0.99 * next_values * (1 - dones) - values
        advantages = self._calculate_gae(deltas, 0.99, 0.95)
        
        # PPO update
        for _ in range(10):  # PPO epochs
            # Actor loss
            probs = self.actor(states)
            dist = torch.distributions.Categorical(probs)
            new_log_probs = dist.log_prob(actions)
            
            ratio = torch.exp(new_log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_param, 1 + self.clip_param) * advantages
            
            actor_loss = -torch.min(surr1, surr2).mean()
            entropy_loss = -self.entropy_coef * dist.entropy().mean()
            
            # Critic loss
            value_pred = self.critic(states).squeeze()
            value_loss = self.value_loss_coef * nn.MSELoss()(value_pred, rewards + 0.99 * next_values * (1 - dones))
            
            # Total loss
            total_loss = actor_loss + value_loss + entropy_loss
            
            # Optimize
            self.actor_optimizer.zero_grad()
            self.critic_optimizer.zero_grad()
            total_loss.backward()
            self.actor_optimizer.step()
            self.critic_optimizer.step()
    
    def _calculate_gae(self, deltas, gamma, lam):
        advantages = []
        gae = 0
        
        for delta in reversed(deltas):
            gae = delta + gamma * lam * gae
            advantages.insert(0, gae)
        
        return torch.FloatTensor(advantages)
```

## 7. 실행 파이프라인

### 7.1 통합 실행 시스템

```python
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging

class MLTradingPipeline:
    def __init__(self, db_path, model_type='ensemble'):
        self.db_path = db_path
        self.model_type = model_type
        self.models = {}
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ml_trading.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def load_data(self, start_date, end_date, stock_codes):
        """
        SQLite 데이터베이스에서 데이터 로드
        """
        conn = sqlite3.connect(self.db_path)
        
        all_data = {}
        for code in stock_codes:
            query = f"""
            SELECT * FROM `{code}`
            WHERE index >= {start_date} AND index <= {end_date}
            ORDER BY index
            """
            
            df = pd.read_sql_query(query, conn)
            df['index'] = pd.to_datetime(df['index'], format='%Y%m%d%H%M%S')
            df.set_index('index', inplace=True)
            
            all_data[code] = df
            self.logger.info(f"Loaded {len(df)} records for {code}")
        
        conn.close()
        return all_data
    
    def prepare_features(self, data):
        """
        특성 엔지니어링 수행
        """
        preprocessor = FeaturePreprocessor()
        
        for code, df in data.items():
            # 기본 특성 전처리
            df = preprocessor.fit_transform(df)
            
            # 시계열 특성 생성
            time_features = create_time_series_features(df)
            df = pd.concat([df, pd.DataFrame(time_features)], axis=1)
            
            # 호가창 불균형 지표
            df['order_imbalance'] = calculate_order_book_imbalance(df)
            
            # 거래 강도 지표
            df['trading_intensity'] = calculate_trading_intensity(df)
            
            data[code] = df
            
        return data
    
    def train_models(self, train_data):
        """
        모델 학습
        """
        if self.model_type == 'ensemble':
            # LightGBM 모델
            lgb_model = LightGBMTradingModel()
            lgb_model.train(
                train_data['features'], 
                train_data['buy_labels'], 
                train_data['sell_labels']
            )
            self.models['lgb'] = lgb_model
            
            # XGBoost 모델
            xgb_model = MultiTimeframeXGBoostModel()
            xgb_model.train_ensemble(
                train_data['features'], 
                train_data['buy_labels']
            )
            self.models['xgb'] = xgb_model
            
        elif self.model_type == 'deep_learning':
            # LSTM 모델
            lstm_model = LSTMTradingModel(
                input_dim=train_data['features'].shape[1]
            )
            lstm_trainer = LSTMTrainer(lstm_model)
            
            # 시퀀스 준비
            sequences, buy_labels, sell_labels = lstm_trainer.prepare_sequences(
                train_data['features']
            )
            
            # DataLoader 생성
            dataset = TensorDataset(
                torch.FloatTensor(sequences),
                torch.FloatTensor(buy_labels),
                torch.FloatTensor(sell_labels)
            )
            dataloader = DataLoader(dataset, batch_size=64, shuffle=True)
            
            # 학습
            for epoch in range(100):
                loss = lstm_trainer.train_epoch(dataloader)
                self.logger.info(f"Epoch {epoch}: Loss = {loss:.4f}")
            
            self.models['lstm'] = lstm_model
            
        elif self.model_type == 'reinforcement':
            # DQN 에이전트
            env = TradingEnvironment(train_data['features'])
            agent = DQNAgent(
                state_size=env.observation_space.shape[0],
                action_size=env.action_space.n
            )
            
            # 학습
            episodes = 1000
            for e in range(episodes):
                state = env.reset()
                total_reward = 0
                
                for time_step in range(500):
                    action = agent.act(state)
                    next_state, reward, done, _ = env.step(action)
                    agent.remember(state, action, reward, next_state, done)
                    state = next_state
                    total_reward += reward
                    
                    if done:
                        break
                
                if len(agent.memory) > 32:
                    agent.replay(32)
                
                self.logger.info(f"Episode {e}: Total Reward = {total_reward:.4f}")
            
            self.models['dqn'] = agent
    
    def backtest(self, test_data):
        """
        백테스팅 수행
        """
        results = {}
        
        for model_name, model in self.models.items():
            if model_name in ['lgb', 'xgb']:
                predictions = model.predict(test_data['features'])
                
            elif model_name == 'lstm':
                trainer = LSTMTrainer(model)
                sequences, _, _ = trainer.prepare_sequences(test_data['features'])
                dataset = TensorDataset(torch.FloatTensor(sequences))
                dataloader = DataLoader(dataset, batch_size=64)
                
                buy_preds, sell_preds = trainer.evaluate(dataloader)
                predictions = {
                    'buy_signal': buy_preds,
                    'sell_signal': sell_preds
                }
                
            elif model_name == 'dqn':
                env = TradingEnvironment(test_data['features'])
                state = env.reset()
                
                actions = []
                for _ in range(len(test_data['features'])):
                    action = model.act(state)
                    actions.append(action)
                    state, _, done, _ = env.step(action)
                    if done:
                        break
                
                predictions = {'actions': actions}
            
            # 성과 평가
            performance = self.evaluate_performance(predictions, test_data)
            results[model_name] = performance
            
        return results
    
    def evaluate_performance(self, predictions, test_data):
        """
        성과 지표 계산
        """
        # 샤프 비율, 최대 낙폭, 수익률 등 계산
        metrics = {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'profit_factor': 0
        }
        
        # 실제 계산 로직 구현
        # ...
        
        return metrics
    
    def optimize_hyperparameters(self):
        """
        베이지안 최적화를 통한 하이퍼파라미터 튜닝
        """
        import optuna
        
        def objective(trial):
            # 하이퍼파라미터 제안
            params = {
                'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.1),
                'num_layers': trial.suggest_int('num_layers', 1, 5),
                'hidden_dim': trial.suggest_int('hidden_dim', 64, 512),
                'dropout': trial.suggest_float('dropout', 0.1, 0.5),
            }
            
            # 모델 학습 및 평가
            # ...
            
            return score
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=100)
        
        return study.best_params

# 실행 예시
if __name__ == "__main__":
    # 파이프라인 초기화
    pipeline = MLTradingPipeline(
        db_path='stock_data.db',
        model_type='ensemble'
    )
    
    # 데이터 로드
    stock_codes = ['005930', '000660', '035720']  # 삼성전자, SK하이닉스, 카카오
    data = pipeline.load_data(
        start_date='20230101',
        end_date='20231231',
        stock_codes=stock_codes
    )
    
    # 특성 준비
    prepared_data = pipeline.prepare_features(data)
    
    # 학습/테스트 분할
    train_size = int(len(prepared_data[stock_codes[0]]) * 0.8)
    train_data = {code: df[:train_size] for code, df in prepared_data.items()}
    test_data = {code: df[train_size:] for code, df in prepared_data.items()}
    
    # 모델 학습
    pipeline.train_models(train_data)
    
    # 백테스팅
    results = pipeline.backtest(test_data)
    
    # 결과 출력
    for model_name, performance in results.items():
        print(f"\n{model_name} Performance:")
        for metric, value in performance.items():
            print(f"  {metric}: {value:.4f}")
```

## 8. 성능 모니터링 및 최적화

### 8.1 실시간 모니터링 시스템

```python
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import seaborn as sns

class PerformanceMonitor:
    def __init__(self):
        self.metrics_history = {
            'accuracy': [],
            'precision': [],
            'recall': [],
            'f1_score': [],
            'profit': [],
            'drawdown': []
        }
        
        self.fig, self.axes = plt.subplots(2, 3, figsize=(15, 8))
        self.fig.suptitle('ML Trading Performance Monitor')
        
    def update_metrics(self, predictions, actuals, portfolio_value):
        """
        실시간 성과 지표 업데이트
        """
        # 분류 성과
        accuracy = accuracy_score(actuals, predictions)
        precision = precision_score(actuals, predictions)
        recall = recall_score(actuals, predictions)
        f1 = f1_score(actuals, predictions)
        
        self.metrics_history['accuracy'].append(accuracy)
        self.metrics_history['precision'].append(precision)
        self.metrics_history['recall'].append(recall)
        self.metrics_history['f1_score'].append(f1)
        
        # 수익 성과
        if len(self.metrics_history['profit']) > 0:
            profit = (portfolio_value / self.metrics_history['profit'][-1] - 1) * 100
        else:
            profit = 0
        
        self.metrics_history['profit'].append(portfolio_value)
        
        # Drawdown 계산
        peak = max(self.metrics_history['profit'])
        drawdown = (portfolio_value - peak) / peak * 100
        self.metrics_history['drawdown'].append(drawdown)
    
    def plot_performance(self):
        """
        성과 시각화
        """
        # Clear previous plots
        for ax in self.axes.flat:
            ax.clear()
        
        # Accuracy
        self.axes[0, 0].plot(self.metrics_history['accuracy'])
        self.axes[0, 0].set_title('Accuracy')
        self.axes[0, 0].set_ylim([0, 1])
        
        # Precision
        self.axes[0, 1].plot(self.metrics_history['precision'])
        self.axes[0, 1].set_title('Precision')
        self.axes[0, 1].set_ylim([0, 1])
        
        # Recall
        self.axes[0, 2].plot(self.metrics_history['recall'])
        self.axes[0, 2].set_title('Recall')
        self.axes[0, 2].set_ylim([0, 1])
        
        # F1 Score
        self.axes[1, 0].plot(self.metrics_history['f1_score'])
        self.axes[1, 0].set_title('F1 Score')
        self.axes[1, 0].set_ylim([0, 1])
        
        # Portfolio Value
        self.axes[1, 1].plot(self.metrics_history['profit'])
        self.axes[1, 1].set_title('Portfolio Value')
        
        # Drawdown
        self.axes[1, 2].fill_between(
            range(len(self.metrics_history['drawdown'])),
            self.metrics_history['drawdown'],
            0,
            color='red',
            alpha=0.3
        )
        self.axes[1, 2].set_title('Drawdown (%)')
        
        plt.tight_layout()
        plt.pause(0.01)
```

## 9. 결론 및 권장사항

### 9.1 구현 우선순위

1. **Phase 1 - 기초 구축** (1-2주)
   - SQLite 데이터베이스 연결 및 데이터 로드
   - 기본 특성 엔지니어링
   - LightGBM 모델 구현 및 테스트

2. **Phase 2 - 고급 모델** (2-3주)
   - LSTM 모델 구현
   - GPU 최적화 적용
   - 앙상블 방법론 구현

3. **Phase 3 - 최적화** (2-3주)
   - 베이지안 하이퍼파라미터 최적화
   - 강화학습 에이전트 구현
   - 실시간 모니터링 시스템

4. **Phase 4 - 실전 적용** (지속적)
   - 백테스팅 검증
   - 실시간 거래 시뮬레이션
   - 성능 개선 및 유지보수

### 9.2 주의사항

1. **과적합 방지**
   - Walk-forward 분석 사용
   - 교차 검증 철저히 수행
   - Out-of-sample 테스트 필수

2. **리스크 관리**
   - 포지션 사이징 전략 수립
   - 최대 손실 한도 설정
   - 다양한 시장 상황 테스트

3. **계산 자원 관리**
   - GPU 메모리 효율적 사용
   - 배치 크기 최적화
   - 데이터 파이프라인 최적화

### 9.3 기대 효과

1. **자동화된 조건식 발견**
   - 수동 작업 대비 1000배 이상 빠른 탐색
   - 인간이 발견하기 어려운 복잡한 패턴 식별

2. **성능 향상**
   - 기존 룰 기반 대비 20-50% 수익률 개선 가능
   - 리스크 조정 수익률 향상

3. **확장성**
   - 새로운 데이터/시장에 쉽게 적용 가능
   - 지속적인 학습을 통한 성능 개선

이 문서는 머신러닝/딥러닝을 활용한 백테스팅 조건식 최적화를 위한 종합적인 가이드입니다. GPU를 효과적으로 활용하여 대규모 데이터를 처리하고, 다양한 모델을 통해 최적의 거래 전략을 자동으로 발견할 수 있습니다.
