# 데이터 파이프라인 구현 가이드

## 1. 데이터 파이프라인 아키텍처

### 1.1 파이프라인 흐름도
```
SQLite DB → Data Loader → Validator → Preprocessor → Feature Engineer → Model Input
     ↑                        ↓                              ↓
     └──── Error Handler ←────┴──────── Cache Manager ←──────┘
```

## 2. SQLite 데이터베이스 연동

### 2.1 데이터베이스 연결 모듈
```python
# core/database.py
import sqlite3
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path

class STOMDatabaseConnector:
    """STOM SQLite 데이터베이스 연결 및 관리"""
    
    def __init__(self, db_path: str, cache_size: int = 100000):
        """
        Args:
            db_path: SQLite 데이터베이스 파일 경로
            cache_size: 메모리 캐시 크기 (행 단위)
        """
        self.db_path = Path(db_path)
        self.cache_size = cache_size
        self.connection = None
        self.logger = logging.getLogger(__name__)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def connect(self) -> sqlite3.Connection:
        """데이터베이스 연결"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # 자동 커밋
            )
            # 성능 최적화 설정
            self.connection.execute("PRAGMA cache_size = 10000")
            self.connection.execute("PRAGMA synchronous = OFF")
            self.connection.execute("PRAGMA journal_mode = MEMORY")
        return self.connection
    
    def get_available_stocks(self) -> List[str]:
        """사용 가능한 종목 코드 조회"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def load_stock_data(
        self, 
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        종목 데이터 로드
        
        Args:
            stock_code: 종목 코드
            start_date: 시작 날짜 (YYYYMMDDHHMMSS)
            end_date: 종료 날짜 (YYYYMMDDHHMMSS)
            columns: 로드할 컬럼 리스트 (None이면 전체)
        
        Returns:
            pandas DataFrame
        """
        # 쿼리 구성
        if columns:
            columns_str = ", ".join(['`index`'] + columns)
        else:
            columns_str = "*"
        
        query = f"SELECT {columns_str} FROM `{stock_code}`"
        
        conditions = []
        if start_date:
            conditions.append(f"`index` >= {start_date}")
        if end_date:
            conditions.append(f"`index` <= {end_date}")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY `index`"
        
        # 데이터 로드
        self.logger.info(f"Loading data for {stock_code}")
        df = pd.read_sql_query(query, self.connect())
        
        # 인덱스 설정
        df['datetime'] = pd.to_datetime(df['index'], format='%Y%m%d%H%M%S')
        df.set_index('datetime', inplace=True)
        
        return df
    
    def load_batch(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        batch_size: int = 100000
    ) -> Dict[str, pd.DataFrame]:
        """
        여러 종목 배치 로드
        
        Args:
            stock_codes: 종목 코드 리스트
            start_date: 시작 날짜
            end_date: 종료 날짜
            batch_size: 배치 크기
        
        Returns:
            종목별 DataFrame 딕셔너리
        """
        result = {}
        
        for code in stock_codes:
            try:
                # 배치 단위로 로드
                chunks = []
                query = f"""
                    SELECT * FROM `{code}`
                    WHERE `index` >= {start_date} AND `index` <= {end_date}
                    ORDER BY `index`
                """
                
                for chunk in pd.read_sql_query(
                    query, 
                    self.connect(), 
                    chunksize=batch_size
                ):
                    chunks.append(chunk)
                
                if chunks:
                    df = pd.concat(chunks, ignore_index=True)
                    df['datetime'] = pd.to_datetime(df['index'], format='%Y%m%d%H%M%S')
                    df.set_index('datetime', inplace=True)
                    result[code] = df
                    self.logger.info(f"Loaded {len(df)} rows for {code}")
                    
            except Exception as e:
                self.logger.error(f"Failed to load {code}: {e}")
                
        return result
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.connection:
            self.connection.close()
            self.connection = None
```

### 2.2 데이터 검증 모듈
```python
# data/validator.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class DataValidator:
    """데이터 품질 검증"""
    
    # STOM 데이터베이스 필수 컬럼
    REQUIRED_COLUMNS = [
        '현재가', '시가', '고가', '저가', '등락율',
        '당일거래대금', '체결강도', '초당매수수량', '초당매도수량'
    ]
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        DataFrame 검증
        
        Returns:
            (검증 성공 여부, 오류 메시지 리스트)
        """
        errors = []
        
        # 1. 필수 컬럼 확인
        missing_cols = set(DataValidator.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # 2. 데이터 타입 확인
        for col in DataValidator.REQUIRED_COLUMNS:
            if col in df.columns:
                if df[col].dtype not in [np.float64, np.int64]:
                    errors.append(f"Invalid dtype for {col}: {df[col].dtype}")
        
        # 3. 널값 확인
        null_counts = df[DataValidator.REQUIRED_COLUMNS].isnull().sum()
        if null_counts.any():
            errors.append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
        
        # 4. 가격 데이터 논리 검증
        if all(col in df.columns for col in ['고가', '저가', '현재가']):
            invalid_prices = df[(df['고가'] < df['저가']) | 
                               (df['현재가'] > df['고가']) | 
                               (df['현재가'] < df['저가'])]
            if not invalid_prices.empty:
                errors.append(f"Invalid price relationships in {len(invalid_prices)} rows")
        
        # 5. 시계열 순서 확인
        if not df.index.is_monotonic_increasing:
            errors.append("Index is not monotonic increasing")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def remove_outliers(
        df: pd.DataFrame, 
        columns: List[str],
        method: str = 'iqr',
        threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        이상치 제거
        
        Args:
            df: 입력 DataFrame
            columns: 이상치 검사할 컬럼
            method: 'iqr' 또는 'zscore'
            threshold: 임계값
        """
        df_clean = df.copy()
        
        for col in columns:
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]
                
            elif method == 'zscore':
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df_clean = df_clean[z_scores < threshold]
        
        return df_clean
```

## 3. 데이터 전처리

### 3.1 전처리 파이프라인
```python
# data/preprocessor.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler, StandardScaler
from typing import Dict, Optional
import pickle

class DataPreprocessor:
    """데이터 전처리 및 정규화"""
    
    def __init__(self):
        self.scalers = {}
        self.feature_stats = {}
        
    def fit(self, df: pd.DataFrame) -> 'DataPreprocessor':
        """
        전처리 파라미터 학습
        
        Args:
            df: 학습 데이터
        """
        # 가격 관련 변수 - RobustScaler (이상치에 강건)
        price_cols = ['현재가', '시가', '고가', '저가']
        price_cols = [col for col in price_cols if col in df.columns]
        if price_cols:
            self.scalers['price'] = RobustScaler()
            self.scalers['price'].fit(df[price_cols])
        
        # 거래량 관련 변수 - 로그 변환 후 StandardScaler
        volume_cols = ['당일거래대금', '초당매수수량', '초당매도수량', '초당거래대금']
        volume_cols = [col for col in volume_cols if col in df.columns]
        if volume_cols:
            # 로그 변환을 위한 최소값 저장
            self.feature_stats['volume_min'] = df[volume_cols].min()
            log_volumes = np.log1p(df[volume_cols] - self.feature_stats['volume_min'] + 1)
            self.scalers['volume'] = StandardScaler()
            self.scalers['volume'].fit(log_volumes)
        
        # 비율 관련 변수 - StandardScaler
        rate_cols = ['등락율', '전일비', '회전율', '체결강도']
        rate_cols = [col for col in rate_cols if col in df.columns]
        if rate_cols:
            self.scalers['rate'] = StandardScaler()
            self.scalers['rate'].fit(df[rate_cols])
        
        # 호가 관련 변수
        order_cols = [col for col in df.columns if '호가' in col or '잔량' in col]
        if order_cols:
            self.scalers['order'] = RobustScaler()
            self.scalers['order'].fit(df[order_cols])
        
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        데이터 변환
        
        Args:
            df: 입력 데이터
            
        Returns:
            변환된 DataFrame
        """
        df_transformed = df.copy()
        
        # 가격 변환
        price_cols = ['현재가', '시가', '고가', '저가']
        price_cols = [col for col in price_cols if col in df.columns]
        if price_cols and 'price' in self.scalers:
            df_transformed[price_cols] = self.scalers['price'].transform(df[price_cols])
        
        # 거래량 변환 (로그 + 정규화)
        volume_cols = ['당일거래대금', '초당매수수량', '초당매도수량', '초당거래대금']
        volume_cols = [col for col in volume_cols if col in df.columns]
        if volume_cols and 'volume' in self.scalers:
            log_volumes = np.log1p(df[volume_cols] - self.feature_stats['volume_min'] + 1)
            df_transformed[volume_cols] = self.scalers['volume'].transform(log_volumes)
        
        # 비율 변환
        rate_cols = ['등락율', '전일비', '회전율', '체결강도']
        rate_cols = [col for col in rate_cols if col in df.columns]
        if rate_cols and 'rate' in self.scalers:
            df_transformed[rate_cols] = self.scalers['rate'].transform(df[rate_cols])
        
        # 호가 변환
        order_cols = [col for col in df.columns if '호가' in col or '잔량' in col]
        if order_cols and 'order' in self.scalers:
            df_transformed[order_cols] = self.scalers['order'].transform(df[order_cols])
        
        # 무한대/NaN 처리
        df_transformed = df_transformed.replace([np.inf, -np.inf], np.nan)
        df_transformed = df_transformed.fillna(0)
        
        return df_transformed
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """학습 및 변환 동시 수행"""
        return self.fit(df).transform(df)
    
    def save(self, filepath: str):
        """전처리기 저장"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'scalers': self.scalers,
                'feature_stats': self.feature_stats
            }, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'DataPreprocessor':
        """전처리기 로드"""
        preprocessor = cls()
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            preprocessor.scalers = data['scalers']
            preprocessor.feature_stats = data['feature_stats']
        return preprocessor
```

## 4. 특성 엔지니어링

### 4.1 기술적 지표 생성
```python
# data/feature_engineer.py
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import talib

class FeatureEngineer:
    """특성 엔지니어링"""
    
    def __init__(self, window_sizes: List[int] = [5, 10, 20, 30, 60]):
        self.window_sizes = window_sizes
        
    def create_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """가격 관련 특성 생성"""
        features = pd.DataFrame(index=df.index)
        
        # 가격 변화율
        features['price_change'] = df['현재가'].pct_change()
        features['high_low_ratio'] = (df['고가'] - df['저가']) / df['저가']
        features['close_to_high'] = (df['고가'] - df['현재가']) / df['고가']
        features['close_to_low'] = (df['현재가'] - df['저가']) / df['저가']
        
        # 이동평균
        for window in self.window_sizes:
            features[f'ma_{window}'] = df['현재가'].rolling(window).mean()
            features[f'ma_ratio_{window}'] = df['현재가'] / features[f'ma_{window}']
            
        # 볼린저 밴드
        for window in self.window_sizes:
            ma = df['현재가'].rolling(window).mean()
            std = df['현재가'].rolling(window).std()
            features[f'bb_upper_{window}'] = ma + (2 * std)
            features[f'bb_lower_{window}'] = ma - (2 * std)
            features[f'bb_width_{window}'] = features[f'bb_upper_{window}'] - features[f'bb_lower_{window}']
            features[f'bb_position_{window}'] = (df['현재가'] - features[f'bb_lower_{window}']) / features[f'bb_width_{window}']
        
        return features
    
    def create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """거래량 관련 특성 생성"""
        features = pd.DataFrame(index=df.index)
        
        # 거래량 변화
        features['volume_change'] = df['당일거래대금'].pct_change()
        
        # 거래 강도
        features['buy_sell_ratio'] = df['초당매수수량'] / (df['초당매도수량'] + 1e-10)
        features['trade_intensity'] = df['초당거래대금'] / df['초당거래대금'].rolling(30).mean()
        
        # 거래량 이동평균
        for window in self.window_sizes:
            features[f'volume_ma_{window}'] = df['당일거래대금'].rolling(window).mean()
            features[f'volume_ratio_{window}'] = df['당일거래대금'] / features[f'volume_ma_{window}']
        
        # VWAP (Volume Weighted Average Price)
        for window in self.window_sizes:
            typical_price = (df['고가'] + df['저가'] + df['현재가']) / 3
            features[f'vwap_{window}'] = (typical_price * df['당일거래대금']).rolling(window).sum() / df['당일거래대금'].rolling(window).sum()
            features[f'vwap_ratio_{window}'] = df['현재가'] / features[f'vwap_{window}']
        
        return features
    
    def create_orderbook_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """호가창 관련 특성 생성"""
        features = pd.DataFrame(index=df.index)
        
        # 호가 스프레드
        features['bid_ask_spread'] = df['매도호가1'] - df['매수호가1']
        features['spread_ratio'] = features['bid_ask_spread'] / df['현재가']
        
        # 호가 잔량 불균형
        bid_columns = [f'매수잔량{i}' for i in range(1, 6)]
        ask_columns = [f'매도잔량{i}' for i in range(1, 6)]
        
        total_bid = df[bid_columns].sum(axis=1)
        total_ask = df[ask_columns].sum(axis=1)
        
        features['order_imbalance'] = (total_bid - total_ask) / (total_bid + total_ask + 1e-10)
        features['bid_ask_volume_ratio'] = total_bid / (total_ask + 1e-10)
        
        # 가중 평균 호가
        bid_prices = [df[f'매수호가{i}'] for i in range(1, 6)]
        ask_prices = [df[f'매도호가{i}'] for i in range(1, 6)]
        bid_volumes = [df[f'매수잔량{i}'] for i in range(1, 6)]
        ask_volumes = [df[f'매도잔량{i}'] for i in range(1, 6)]
        
        weighted_bid = sum(p * v for p, v in zip(bid_prices, bid_volumes)) / (total_bid + 1e-10)
        weighted_ask = sum(p * v for p, v in zip(ask_prices, ask_volumes)) / (total_ask + 1e-10)
        
        features['weighted_mid_price'] = (weighted_bid + weighted_ask) / 2
        features['price_to_weighted_mid'] = df['현재가'] / features['weighted_mid_price']
        
        # 호가 압력
        features['bid_pressure'] = sum(df[f'매수잔량{i}'] * (6-i) for i in range(1, 6)) / total_bid
        features['ask_pressure'] = sum(df[f'매도잔량{i}'] * (6-i) for i in range(1, 6)) / total_ask
        
        return features
    
    def create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 생성"""
        features = pd.DataFrame(index=df.index)
        
        # RSI
        for window in [14, 28]:
            features[f'rsi_{window}'] = talib.RSI(df['현재가'].values, timeperiod=window)
        
        # MACD
        macd, signal, hist = talib.MACD(df['현재가'].values, fastperiod=12, slowperiod=26, signalperiod=9)
        features['macd'] = macd
        features['macd_signal'] = signal
        features['macd_hist'] = hist
        
        # Stochastic
        slowk, slowd = talib.STOCH(df['고가'].values, df['저가'].values, df['현재가'].values,
                                   fastk_period=14, slowk_period=3, slowd_period=3)
        features['stoch_k'] = slowk
        features['stoch_d'] = slowd
        
        # ATR (Average True Range)
        features['atr'] = talib.ATR(df['고가'].values, df['저가'].values, df['현재가'].values, timeperiod=14)
        features['atr_ratio'] = features['atr'] / df['현재가']
        
        # ADX (Average Directional Index)
        features['adx'] = talib.ADX(df['고가'].values, df['저가'].values, df['현재가'].values, timeperiod=14)
        
        # CCI (Commodity Channel Index)
        features['cci'] = talib.CCI(df['고가'].values, df['저가'].values, df['현재가'].values, timeperiod=20)
        
        # Williams %R
        features['williams_r'] = talib.WILLR(df['고가'].values, df['저가'].values, df['현재가'].values, timeperiod=14)
        
        return features
    
    def create_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """패턴 인식 특성"""
        features = pd.DataFrame(index=df.index)
        
        # 캔들 패턴
        open_prices = df['시가'].values
        high_prices = df['고가'].values
        low_prices = df['저가'].values
        close_prices = df['현재가'].values
        
        # 해머
        features['hammer'] = talib.CDLHAMMER(open_prices, high_prices, low_prices, close_prices)
        
        # 도지
        features['doji'] = talib.CDLDOJI(open_prices, high_prices, low_prices, close_prices)
        
        # 엔걸핑
        features['engulfing'] = talib.CDLENGULFING(open_prices, high_prices, low_prices, close_prices)
        
        # 모닝스타
        features['morning_star'] = talib.CDLMORNINGSTAR(open_prices, high_prices, low_prices, close_prices)
        
        # 슈팅스타
        features['shooting_star'] = talib.CDLSHOOTINGSTAR(open_prices, high_prices, low_prices, close_prices)
        
        return features
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """모든 특성 생성"""
        all_features = [
            self.create_price_features(df),
            self.create_volume_features(df),
            self.create_orderbook_features(df),
            self.create_technical_indicators(df),
            self.create_pattern_features(df)
        ]
        
        # 모든 특성 결합
        result = pd.concat(all_features, axis=1)
        
        # NaN 처리
        result = result.fillna(method='ffill').fillna(0)
        
        return result
```

## 5. 데이터 파이프라인 통합

### 5.1 통합 파이프라인
```python
# data/pipeline.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import joblib

from core.database import STOMDatabaseConnector
from data.validator import DataValidator
from data.preprocessor import DataPreprocessor
from data.feature_engineer import FeatureEngineer

class DataPipeline:
    """통합 데이터 파이프라인"""
    
    def __init__(
        self,
        db_path: str,
        cache_dir: str = './cache',
        use_cache: bool = True
    ):
        """
        Args:
            db_path: 데이터베이스 경로
            cache_dir: 캐시 디렉토리
            use_cache: 캐시 사용 여부
        """
        self.db_connector = STOMDatabaseConnector(db_path)
        self.validator = DataValidator()
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.use_cache = use_cache
        
        self.logger = logging.getLogger(__name__)
    
    def prepare_training_data(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        target_holding_period: int = 10,
        test_split: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        학습 데이터 준비
        
        Args:
            stock_codes: 종목 코드 리스트
            start_date: 시작 날짜
            end_date: 종료 날짜
            target_holding_period: 타겟 보유 기간 (틱)
            test_split: 테스트 데이터 비율
            
        Returns:
            (X_train, X_test, y_train, y_test)
        """
        # 캐시 확인
        cache_key = f"{'-'.join(stock_codes)}_{start_date}_{end_date}"
        cache_path = self.cache_dir / f"{cache_key}.pkl"
        
        if self.use_cache and cache_path.exists():
            self.logger.info(f"Loading from cache: {cache_path}")
            return joblib.load(cache_path)
        
        # 데이터 로드
        all_data = []
        for code in stock_codes:
            self.logger.info(f"Processing {code}")
            
            # 1. 데이터 로드
            df = self.db_connector.load_stock_data(code, start_date, end_date)
            
            # 2. 검증
            is_valid, errors = self.validator.validate_dataframe(df)
            if not is_valid:
                self.logger.warning(f"Validation errors for {code}: {errors}")
                df = self.validator.remove_outliers(df, ['현재가', '당일거래대금'])
            
            # 3. 특성 생성
            features = self.feature_engineer.create_all_features(df)
            
            # 4. 원본 데이터와 결합
            df_combined = pd.concat([df, features], axis=1)
            
            # 5. 타겟 생성 (미래 수익률)
            df_combined['target'] = (
                df['현재가'].shift(-target_holding_period) / df['현재가'] - 1
            ) * 100
            
            # 이진 분류 타겟 (1% 이상 상승 시 1)
            df_combined['target_binary'] = (df_combined['target'] > 1.0).astype(int)
            
            # 종목 코드 추가
            df_combined['stock_code'] = code
            
            all_data.append(df_combined)
        
        # 모든 데이터 결합
        combined_df = pd.concat(all_data, axis=0)
        
        # NaN 제거
        combined_df = combined_df.dropna(subset=['target_binary'])
        
        # 6. 전처리
        feature_columns = [col for col in combined_df.columns 
                          if col not in ['target', 'target_binary', 'stock_code', 'index']]
        
        X = combined_df[feature_columns]
        y = combined_df['target_binary']
        
        # 학습/테스트 분할 (시간 순서 유지)
        split_idx = int(len(X) * (1 - test_split))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # 전처리
        X_train = self.preprocessor.fit_transform(X_train)
        X_test = self.preprocessor.transform(X_test)
        
        # 캐시 저장
        if self.use_cache:
            joblib.dump((X_train, X_test, y_train, y_test), cache_path)
            self.logger.info(f"Saved to cache: {cache_path}")
        
        return X_train, X_test, y_train, y_test
    
    def prepare_realtime_data(
        self,
        stock_code: str,
        lookback_period: int = 100
    ) -> pd.DataFrame:
        """
        실시간 예측용 데이터 준비
        
        Args:
            stock_code: 종목 코드
            lookback_period: 과거 데이터 참조 기간
            
        Returns:
            전처리된 특성 DataFrame
        """
        # 최근 데이터 로드
        df = self.db_connector.load_stock_data(
            stock_code,
            columns=None  # 모든 컬럼
        )
        
        # 최근 N개 데이터만 사용
        df = df.tail(lookback_period + 100)  # 특성 생성을 위한 여유분
        
        # 특성 생성
        features = self.feature_engineer.create_all_features(df)
        
        # 원본 데이터와 결합
        df_combined = pd.concat([df, features], axis=1)
        
        # 필요한 컬럼만 선택
        feature_columns = [col for col in df_combined.columns 
                          if col not in ['index', 'stock_code']]
        
        X = df_combined[feature_columns].tail(lookback_period)
        
        # 전처리
        X = self.preprocessor.transform(X)
        
        return X
```

## 6. 사용 예제

### 6.1 기본 사용법
```python
# example_usage.py
from data.pipeline import DataPipeline
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# 파이프라인 초기화
pipeline = DataPipeline(
    db_path='./stock_data.db',
    cache_dir='./cache',
    use_cache=True
)

# 학습 데이터 준비
stock_codes = ['005930', '000660', '035720']  # 삼성전자, SK하이닉스, 카카오
X_train, X_test, y_train, y_test = pipeline.prepare_training_data(
    stock_codes=stock_codes,
    start_date='20220101000000',
    end_date='20231231235959',
    target_holding_period=10,  # 10틱 후 수익률 예측
    test_split=0.2
)

print(f"Training data shape: {X_train.shape}")
print(f"Test data shape: {X_test.shape}")
print(f"Features: {X_train.columns.tolist()[:10]}...")  # 처음 10개 특성만 출력
print(f"Target distribution:")
print(y_train.value_counts(normalize=True))

# 실시간 데이터 준비
realtime_data = pipeline.prepare_realtime_data(
    stock_code='005930',
    lookback_period=100
)

print(f"Realtime data shape: {realtime_data.shape}")
```

## 7. 성능 최적화 팁

### 7.1 메모리 최적화
```python
# 데이터 타입 최적화
def optimize_dtypes(df):
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != 'object':
            c_min = df[col].min()
            c_max = df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
    
    return df
```

### 7.2 병렬 처리
```python
from joblib import Parallel, delayed

def process_stock_parallel(stock_codes, n_jobs=-1):
    """병렬로 여러 종목 처리"""
    results = Parallel(n_jobs=n_jobs)(
        delayed(process_single_stock)(code) for code in stock_codes
    )
    return results
```

## 8. 다음 단계

1. **GPU 가속 적용**
   - CuDF를 사용한 DataFrame 연산
   - CuPy를 사용한 배열 연산

2. **스트리밍 데이터 처리**
   - 실시간 데이터 수신 및 처리
   - 증분 특성 업데이트

3. **특성 선택**
   - 중요도 기반 특성 선택
   - 차원 축소 (PCA, AutoEncoder)
