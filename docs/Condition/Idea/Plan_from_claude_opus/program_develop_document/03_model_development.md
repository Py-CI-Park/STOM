# 단계별 모델 개발 가이드

## Phase 1: LightGBM 프로토타입 (1주차)

### 1.1 LightGBM 기본 모델 구현

```python
# models/lightgbm_model.py
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import optuna
from typing import Dict, Tuple, Optional
import pickle
import logging

class LightGBMTrader:
    """LightGBM 기반 거래 모델"""
    
    def __init__(self, task_type: str = 'classification'):
        """
        Args:
            task_type: 'classification' 또는 'regression'
        """
        self.task_type = task_type
        self.model = None
        self.best_params = None
        self.feature_importance = None
        self.logger = logging.getLogger(__name__)
        
    def optimize_hyperparameters(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        cv_folds: int = 5
    ) -> Dict:
        """
        Optuna를 사용한 베이지안 하이퍼파라미터 최적화
        
        Args:
            X_train: 학습 데이터
            y_train: 타겟 데이터
            n_trials: 시도 횟수
            cv_folds: 교차 검증 폴드 수
            
        Returns:
            최적 파라미터 딕셔너리
        """
        def objective(trial):
            params = {
                'objective': 'binary' if self.task_type == 'classification' else 'regression',
                'metric': 'binary_logloss' if self.task_type == 'classification' else 'rmse',
                'boosting_type': 'gbdt',
                'num_leaves': trial.suggest_int('num_leaves', 20, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
                'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
                'bagging_freq': trial.suggest_int('bagging_freq', 1, 7),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
                'lambda_l1': trial.suggest_float('lambda_l1', 1e-8, 10.0, log=True),
                'lambda_l2': trial.suggest_float('lambda_l2', 1e-8, 10.0, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 12),
                'min_gain_to_split': trial.suggest_float('min_gain_to_split', 0, 15),
                'random_state': 42,
                'verbosity': -1
            }
            
            # 시계열 교차 검증
            tscv = TimeSeriesSplit(n_splits=cv_folds)
            scores = []
            
            for train_idx, val_idx in tscv.split(X_train):
                X_fold_train = X_train.iloc[train_idx]
                X_fold_val = X_train.iloc[val_idx]
                y_fold_train = y_train.iloc[train_idx]
                y_fold_val = y_train.iloc[val_idx]
                
                # LightGBM 데이터셋 생성
                train_data = lgb.Dataset(X_fold_train, label=y_fold_train)
                val_data = lgb.Dataset(X_fold_val, label=y_fold_val, reference=train_data)
                
                # 모델 학습
                model = lgb.train(
                    params,
                    train_data,
                    valid_sets=[val_data],
                    num_boost_round=1000,
                    callbacks=[
                        lgb.early_stopping(100),
                        lgb.log_evaluation(0)
                    ]
                )
                
                # 예측 및 평가
                predictions = model.predict(X_fold_val, num_iteration=model.best_iteration)
                
                if self.task_type == 'classification':
                    predictions_binary = (predictions > 0.5).astype(int)
                    score = f1_score(y_fold_val, predictions_binary)
                else:
                    score = -np.sqrt(np.mean((predictions - y_fold_val) ** 2))  # RMSE (음수)
                
                scores.append(score)
            
            return np.mean(scores)
        
        # Optuna 스터디 생성 및 최적화
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        self.logger.info(f"Best trial: {study.best_trial.params}")
        self.logger.info(f"Best score: {study.best_value}")
        
        self.best_params = study.best_trial.params
        self.best_params['objective'] = 'binary' if self.task_type == 'classification' else 'regression'
        self.best_params['metric'] = 'binary_logloss' if self.task_type == 'classification' else 'rmse'
        self.best_params['random_state'] = 42
        self.best_params['verbosity'] = -1
        
        return self.best_params
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        params: Optional[Dict] = None
    ):
        """
        모델 학습
        
        Args:
            X_train: 학습 데이터
            y_train: 학습 타겟
            X_val: 검증 데이터
            y_val: 검증 타겟
            params: 하이퍼파라미터 (None이면 기본값 사용)
        """
        if params is None:
            params = self.best_params if self.best_params else self._get_default_params()
        
        # 데이터셋 생성
        train_data = lgb.Dataset(X_train, label=y_train)
        valid_sets = [train_data]
        
        if X_val is not None and y_val is not None:
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            valid_sets.append(val_data)
        
        # 모델 학습
        self.model = lgb.train(
            params,
            train_data,
            valid_sets=valid_sets,
            num_boost_round=2000,
            callbacks=[
                lgb.early_stopping(100),
                lgb.log_evaluation(100)
            ]
        )
        
        # 특성 중요도 저장
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importance(importance_type='gain')
        }).sort_values('importance', ascending=False)
        
        self.logger.info(f"Training completed. Best iteration: {self.model.best_iteration}")
        self.logger.info(f"Top 10 features:\n{self.feature_importance.head(10)}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """예측"""
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        predictions = self.model.predict(X, num_iteration=self.model.best_iteration)
        
        if self.task_type == 'classification':
            return predictions  # 확률값 반환
        else:
            return predictions
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """확률 예측 (분류 전용)"""
        if self.task_type != 'classification':
            raise ValueError("predict_proba is only for classification")
        
        return self.predict(X)
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """모델 평가"""
        predictions = self.predict(X)
        
        if self.task_type == 'classification':
            predictions_binary = (predictions > 0.5).astype(int)
            
            metrics = {
                'accuracy': accuracy_score(y, predictions_binary),
                'precision': precision_score(y, predictions_binary),
                'recall': recall_score(y, predictions_binary),
                'f1': f1_score(y, predictions_binary),
                'auc': roc_auc_score(y, predictions)
            }
        else:
            metrics = {
                'rmse': np.sqrt(np.mean((predictions - y) ** 2)),
                'mae': np.mean(np.abs(predictions - y)),
                'mape': np.mean(np.abs((y - predictions) / y)) * 100
            }
        
        return metrics
    
    def save(self, filepath: str):
        """모델 저장"""
        model_data = {
            'model': self.model,
            'best_params': self.best_params,
            'feature_importance': self.feature_importance,
            'task_type': self.task_type
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        self.logger.info(f"Model saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'LightGBMTrader':
        """모델 로드"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        instance = cls(task_type=model_data['task_type'])
        instance.model = model_data['model']
        instance.best_params = model_data['best_params']
        instance.feature_importance = model_data['feature_importance']
        
        return instance
    
    def _get_default_params(self) -> Dict:
        """기본 파라미터"""
        return {
            'objective': 'binary' if self.task_type == 'classification' else 'regression',
            'metric': 'binary_logloss' if self.task_type == 'classification' else 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'random_state': 42,
            'verbosity': -1
        }
```

### 1.2 Phase 1 실행 스크립트

```python
# scripts/train_phase1.py
import sys
import logging
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from data.pipeline import DataPipeline
from models.lightgbm_model import LightGBMTrader
import pandas as pd
import numpy as np

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # 1. 데이터 준비
    print("=" * 50)
    print("Phase 1: LightGBM 프로토타입")
    print("=" * 50)
    
    print("\n1. 데이터 로딩...")
    pipeline = DataPipeline(
        db_path='./data/stock_data.db',
        cache_dir='./cache'
    )
    
    stock_codes = ['005930', '000660']  # 삼성전자, SK하이닉스
    X_train, X_test, y_train, y_test = pipeline.prepare_training_data(
        stock_codes=stock_codes,
        start_date='20220101000000',
        end_date='20231231235959',
        target_holding_period=10,
        test_split=0.2
    )
    
    print(f"학습 데이터: {X_train.shape}")
    print(f"테스트 데이터: {X_test.shape}")
    print(f"타겟 분포:\n{y_train.value_counts(normalize=True)}")
    
    # 2. 하이퍼파라미터 최적화
    print("\n2. 하이퍼파라미터 최적화...")
    model = LightGBMTrader(task_type='classification')
    
    best_params = model.optimize_hyperparameters(
        X_train, y_train,
        n_trials=20,  # 빠른 테스트를 위해 적은 수로 설정
        cv_folds=3
    )
    
    print(f"최적 파라미터: {best_params}")
    
    # 3. 모델 학습
    print("\n3. 모델 학습...")
    model.train(X_train, y_train, X_test, y_test, params=best_params)
    
    # 4. 평가
    print("\n4. 모델 평가...")
    train_metrics = model.evaluate(X_train, y_train)
    test_metrics = model.evaluate(X_test, y_test)
    
    print("학습 데이터 성능:")
    for metric, value in train_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\n테스트 데이터 성능:")
    for metric, value in test_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # 5. 특성 중요도
    print("\n5. Top 20 중요 특성:")
    print(model.feature_importance.head(20))
    
    # 6. 모델 저장
    print("\n6. 모델 저장...")
    model.save('./models/lightgbm_phase1.pkl')
    
    print("\n✅ Phase 1 완료!")
    
if __name__ == "__main__":
    main()
```

## Phase 2: LSTM 딥러닝 모델 (2-3주차)

### 2.1 LSTM 모델 구현

```python
# models/lstm_model.py
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict
from sklearn.preprocessing import StandardScaler
import logging

class StockDataset(Dataset):
    """주식 데이터셋"""
    
    def __init__(self, X: np.ndarray, y: np.ndarray, seq_length: int = 60):
        """
        Args:
            X: 특성 데이터 (n_samples, n_features)
            y: 타겟 데이터 (n_samples,)
            seq_length: 시퀀스 길이
        """
        self.seq_length = seq_length
        self.X = X
        self.y = y
        
    def __len__(self):
        return len(self.X) - self.seq_length + 1
    
    def __getitem__(self, idx):
        # 시퀀스 데이터 생성
        X_seq = self.X[idx:idx + self.seq_length]
        y_target = self.y[idx + self.seq_length - 1]
        
        return torch.FloatTensor(X_seq), torch.FloatTensor([y_target])

class LSTMModel(nn.Module):
    """LSTM 거래 모델"""
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 256,
        num_layers: int = 3,
        dropout: float = 0.2,
        bidirectional: bool = True
    ):
        super(LSTMModel, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        
        # LSTM 레이어
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        # Attention 메커니즘
        lstm_output_dim = hidden_dim * 2 if bidirectional else hidden_dim
        self.attention = nn.MultiheadAttention(
            lstm_output_dim,
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        # Fully Connected 레이어
        self.fc_layers = nn.Sequential(
            nn.Linear(lstm_output_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.BatchNorm1d(256),
            
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.BatchNorm1d(128),
            
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Self-Attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # 마지막 타임스텝 또는 평균 풀링
        # out = attn_out[:, -1, :]  # 마지막 타임스텝
        out = torch.mean(attn_out, dim=1)  # 평균 풀링
        
        # Fully Connected
        out = self.fc_layers(out)
        
        return out

class LSTMTrader:
    """LSTM 트레이더"""
    
    def __init__(
        self,
        input_dim: int,
        seq_length: int = 60,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.input_dim = input_dim
        self.seq_length = seq_length
        self.device = torch.device(device)
        self.model = None
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Using device: {self.device}")
    
    def build_model(
        self,
        hidden_dim: int = 256,
        num_layers: int = 3,
        dropout: float = 0.2
    ):
        """모델 구축"""
        self.model = LSTMModel(
            self.input_dim,
            hidden_dim,
            num_layers,
            dropout
        ).to(self.device)
        
        self.logger.info(f"Model built with {sum(p.numel() for p in self.model.parameters())} parameters")
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 100,
        batch_size: int = 64,
        learning_rate: float = 0.001,
        early_stopping_patience: int = 10
    ):
        """모델 학습"""
        # 데이터 정규화
        X_train = self.scaler.fit_transform(X_train)
        if X_val is not None:
            X_val = self.scaler.transform(X_val)
        
        # 데이터셋 생성
        train_dataset = StockDataset(X_train, y_train, self.seq_length)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        if X_val is not None and y_val is not None:
            val_dataset = StockDataset(X_val, y_val, self.seq_length)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # 모델이 없으면 생성
        if self.model is None:
            self.build_model()
        
        # 옵티마이저 및 손실 함수
        optimizer = optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=0.01)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        criterion = nn.BCELoss()
        
        # 학습
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0
            train_correct = 0
            train_total = 0
            
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                
                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                
                optimizer.step()
                
                train_loss += loss.item()
                predicted = (outputs > 0.5).float()
                train_correct += (predicted == batch_y).sum().item()
                train_total += batch_y.size(0)
            
            avg_train_loss = train_loss / len(train_loader)
            train_accuracy = train_correct / train_total
            
            # Validation
            if X_val is not None:
                self.model.eval()
                val_loss = 0
                val_correct = 0
                val_total = 0
                
                with torch.no_grad():
                    for batch_x, batch_y in val_loader:
                        batch_x = batch_x.to(self.device)
                        batch_y = batch_y.to(self.device)
                        
                        outputs = self.model(batch_x)
                        loss = criterion(outputs, batch_y)
                        
                        val_loss += loss.item()
                        predicted = (outputs > 0.5).float()
                        val_correct += (predicted == batch_y).sum().item()
                        val_total += batch_y.size(0)
                
                avg_val_loss = val_loss / len(val_loader)
                val_accuracy = val_correct / val_total
                
                # Early stopping
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                    # 최고 모델 저장
                    torch.save(self.model.state_dict(), 'best_lstm_model.pth')
                else:
                    patience_counter += 1
                
                if patience_counter >= early_stopping_patience:
                    self.logger.info(f"Early stopping at epoch {epoch}")
                    break
                
                self.logger.info(
                    f"Epoch {epoch+1}/{epochs} - "
                    f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_accuracy:.4f}, "
                    f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_accuracy:.4f}"
                )
            else:
                self.logger.info(
                    f"Epoch {epoch+1}/{epochs} - "
                    f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_accuracy:.4f}"
                )
            
            scheduler.step()
        
        # 최고 모델 로드
        if X_val is not None:
            self.model.load_state_dict(torch.load('best_lstm_model.pth'))
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """예측"""
        self.model.eval()
        
        # 정규화
        X = self.scaler.transform(X)
        
        # 데이터셋 생성
        dataset = StockDataset(X, np.zeros(len(X)), self.seq_length)
        loader = DataLoader(dataset, batch_size=64, shuffle=False)
        
        predictions = []
        
        with torch.no_grad():
            for batch_x, _ in loader:
                batch_x = batch_x.to(self.device)
                outputs = self.model(batch_x)
                predictions.extend(outputs.cpu().numpy())
        
        return np.array(predictions).flatten()
    
    def save(self, filepath: str):
        """모델 저장"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler': self.scaler,
            'input_dim': self.input_dim,
            'seq_length': self.seq_length
        }, filepath)
        
        self.logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """모델 로드"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.input_dim = checkpoint['input_dim']
        self.seq_length = checkpoint['seq_length']
        self.scaler = checkpoint['scaler']
        
        self.build_model()
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        self.logger.info(f"Model loaded from {filepath}")
```

### 2.2 GPU 최적화 적용

```python
# models/gpu_optimizer.py
import torch
from torch.cuda.amp import autocast, GradScaler
import cupy as cp
import numpy as np
from typing import Tuple

class GPUOptimizer:
    """GPU 최적화 유틸리티"""
    
    @staticmethod
    def check_gpu_availability():
        """GPU 사용 가능 여부 확인"""
        print("=" * 50)
        print("GPU 정보")
        print("=" * 50)
        
        if torch.cuda.is_available():
            print(f"PyTorch CUDA 사용 가능: {torch.cuda.is_available()}")
            print(f"CUDA 버전: {torch.version.cuda}")
            print(f"GPU 개수: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                print(f"\nGPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"  메모리: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
                print(f"  Compute Capability: {torch.cuda.get_device_properties(i).major}.{torch.cuda.get_device_properties(i).minor}")
        else:
            print("CUDA를 사용할 수 없습니다. CPU 모드로 실행됩니다.")
        
        try:
            import cupy as cp
            print(f"\nCuPy 사용 가능: True")
            print(f"CuPy 버전: {cp.__version__}")
        except ImportError:
            print("\nCuPy를 사용할 수 없습니다.")
    
    @staticmethod
    def optimize_batch_size(model, sample_input_shape: Tuple, max_batch_size: int = 512):
        """최적 배치 크기 찾기"""
        device = next(model.parameters()).device
        batch_size = 1
        optimal_batch_size = 1
        
        while batch_size <= max_batch_size:
            try:
                # 테스트 입력 생성
                test_input = torch.randn(batch_size, *sample_input_shape).to(device)
                
                # Forward pass
                with torch.no_grad():
                    _ = model(test_input)
                
                optimal_batch_size = batch_size
                batch_size *= 2
                
                # 메모리 정리
                del test_input
                torch.cuda.empty_cache()
                
            except RuntimeError as e:
                if "out of memory" in str(e):
                    print(f"메모리 부족: 배치 크기 {batch_size}")
                    break
                else:
                    raise e
        
        print(f"최적 배치 크기: {optimal_batch_size}")
        return optimal_batch_size
    
    @staticmethod
    def mixed_precision_training(model, train_loader, optimizer, criterion, device):
        """Mixed Precision Training 예제"""
        scaler = GradScaler()
        
        model.train()
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            
            optimizer.zero_grad()
            
            # Mixed precision
            with autocast():
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
            
            # Backward pass with scaling
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        
        return loss.item()
```

## Phase 3: 앙상블 및 고급 기능 (4-5주차)

### 3.1 앙상블 모델

```python
# models/ensemble.py
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
import pickle
from sklearn.ensemble import VotingClassifier
from sklearn.base import BaseEstimator, ClassifierMixin

class EnsembleTrader(BaseEstimator, ClassifierMixin):
    """앙상블 거래 모델"""
    
    def __init__(
        self,
        models: Dict[str, any],
        weights: Optional[Dict[str, float]] = None,
        voting: str = 'soft'
    ):
        """
        Args:
            models: 모델 딕셔너리 {'model_name': model_instance}
            weights: 모델별 가중치
            voting: 'hard' 또는 'soft'
        """
        self.models = models
        self.weights = weights or {name: 1.0 for name in models.keys()}
        self.voting = voting
        
    def fit(self, X, y):
        """학습 (이미 학습된 모델 사용)"""
        return self
    
    def predict_proba(self, X):
        """확률 예측"""
        predictions = {}
        
        for name, model in self.models.items():
            if hasattr(model, 'predict_proba'):
                pred = model.predict_proba(X)
            else:
                pred = model.predict(X)
            
            # 이진 분류인 경우 positive class 확률만
            if len(pred.shape) == 1:
                predictions[name] = pred
            else:
                predictions[name] = pred[:, 1]
        
        # 가중 평균
        weighted_preds = np.zeros(len(X))
        total_weight = sum(self.weights.values())
        
        for name, pred in predictions.items():
            weighted_preds += pred * self.weights[name] / total_weight
        
        # 이진 분류용 형태로 변환
        proba = np.column_stack([1 - weighted_preds, weighted_preds])
        
        return proba
    
    def predict(self, X):
        """예측"""
        if self.voting == 'soft':
            proba = self.predict_proba(X)
            return (proba[:, 1] > 0.5).astype(int)
        else:
            # Hard voting
            predictions = []
            for name, model in self.models.items():
                pred = model.predict(X)
                predictions.append(pred)
            
            # 다수결
            predictions = np.array(predictions)
            return np.apply_along_axis(
                lambda x: np.bincount(x).argmax(), 
                axis=0, 
                arr=predictions
            )
    
    def evaluate(self, X, y):
        """평가"""
        from sklearn.metrics import classification_report, confusion_matrix
        
        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)[:, 1]
        
        print("Confusion Matrix:")
        print(confusion_matrix(y, y_pred))
        print("\nClassification Report:")
        print(classification_report(y, y_pred))
        
        # 개별 모델 성능
        print("\n개별 모델 성능:")
        for name, model in self.models.items():
            if hasattr(model, 'evaluate'):
                metrics = model.evaluate(X, y)
                print(f"\n{name}:")
                for metric, value in metrics.items():
                    print(f"  {metric}: {value:.4f}")
```

### 3.2 통합 실행 스크립트

```python
# scripts/train_full_pipeline.py
import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))

from data.pipeline import DataPipeline
from models.lightgbm_model import LightGBMTrader
from models.lstm_model import LSTMTrader
from models.ensemble import EnsembleTrader
from models.gpu_optimizer import GPUOptimizer

def main():
    print("=" * 60)
    print("STOM ML/DL 백테스팅 최적화 시스템 - 전체 파이프라인")
    print("=" * 60)
    
    # GPU 확인
    GPUOptimizer.check_gpu_availability()
    
    # 1. 데이터 준비
    print("\n" + "=" * 60)
    print("1. 데이터 준비")
    print("=" * 60)
    
    pipeline = DataPipeline(
        db_path='./data/stock_data.db',
        cache_dir='./cache'
    )
    
    stock_codes = ['005930', '000660', '035720']
    X_train, X_test, y_train, y_test = pipeline.prepare_training_data(
        stock_codes=stock_codes,
        start_date='20220101000000',
        end_date='20231231235959',
        target_holding_period=10,
        test_split=0.2
    )
    
    print(f"✅ 데이터 로드 완료")
    print(f"  - 학습: {X_train.shape}")
    print(f"  - 테스트: {X_test.shape}")
    
    # 2. LightGBM 모델
    print("\n" + "=" * 60)
    print("2. LightGBM 모델 학습")
    print("=" * 60)
    
    lgb_model = LightGBMTrader(task_type='classification')
    
    # 하이퍼파라미터 최적화 (간단하게)
    lgb_model.train(X_train, y_train, X_test, y_test)
    lgb_metrics = lgb_model.evaluate(X_test, y_test)
    
    print("✅ LightGBM 성능:")
    for metric, value in lgb_metrics.items():
        print(f"  - {metric}: {value:.4f}")
    
    # 3. LSTM 모델
    print("\n" + "=" * 60)
    print("3. LSTM 모델 학습")
    print("=" * 60)
    
    lstm_model = LSTMTrader(
        input_dim=X_train.shape[1],
        seq_length=30
    )
    
    # NumPy 배열로 변환
    X_train_np = X_train.values if hasattr(X_train, 'values') else X_train
    X_test_np = X_test.values if hasattr(X_test, 'values') else X_test
    y_train_np = y_train.values if hasattr(y_train, 'values') else y_train
    y_test_np = y_test.values if hasattr(y_test, 'values') else y_test
    
    # 학습 데이터가 충분한지 확인
    if len(X_train_np) > lstm_model.seq_length:
        lstm_model.train(
            X_train_np, y_train_np,
            X_test_np, y_test_np,
            epochs=20,  # 빠른 테스트
            batch_size=32
        )
        
        # LSTM 예측
        lstm_pred = lstm_model.predict(X_test_np)
        lstm_acc = np.mean((lstm_pred > 0.5) == y_test_np)
        
        print(f"✅ LSTM 정확도: {lstm_acc:.4f}")
    else:
        print("⚠️ LSTM 학습을 위한 데이터가 부족합니다.")
        lstm_model = None
    
    # 4. 앙상블 모델
    print("\n" + "=" * 60)
    print("4. 앙상블 모델")
    print("=" * 60)
    
    models = {'LightGBM': lgb_model}
    weights = {'LightGBM': 1.0}
    
    if lstm_model is not None:
        models['LSTM'] = lstm_model
        weights['LSTM'] = 0.8
    
    ensemble = EnsembleTrader(
        models=models,
        weights=weights,
        voting='soft'
    )
    
    # 앙상블 평가
    ensemble.evaluate(X_test, y_test)
    
    # 5. 최종 결과
    print("\n" + "=" * 60)
    print("5. 최종 결과 요약")
    print("=" * 60)
    
    print("\n✅ 전체 파이프라인 실행 완료!")
    print("\n주요 성과:")
    print(f"  - LightGBM F1 Score: {lgb_metrics['f1']:.4f}")
    if lstm_model:
        print(f"  - LSTM Accuracy: {lstm_acc:.4f}")
    print(f"  - 특성 개수: {X_train.shape[1]}")
    print(f"  - 학습 데이터: {X_train.shape[0]} 샘플")
    
    print("\n📊 다음 단계:")
    print("  1. 백테스팅 시뮬레이션 실행")
    print("  2. 실시간 예측 API 구축")
    print("  3. 성과 모니터링 대시보드 개발")

if __name__ == "__main__":
    main()
```

## 실행 가이드

### 환경 설정

```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 필수 패키지 설치
pip install -r requirements.txt

# 3. CUDA 설정 (GPU 사용 시)
# NVIDIA 드라이버 및 CUDA Toolkit 11.8+ 설치 필요
```

### requirements.txt

```txt
# Core
pandas>=1.5.0
numpy>=1.24.0
scikit-learn>=1.3.0
sqlite3

# Machine Learning
lightgbm>=4.0.0
xgboost>=1.7.0
optuna>=3.3.0

# Deep Learning
torch>=2.0.0
torchvision>=0.15.0

# GPU Acceleration
cupy-cuda118>=12.0.0  # CUDA 버전에 맞게 조정
cudf-cu118>=23.0.0    # Optional

# Technical Indicators
ta-lib>=0.4.0

# Visualization
matplotlib>=3.6.0
seaborn>=0.12.0
plotly>=5.14.0

# API
fastapi>=0.100.0
uvicorn>=0.23.0

# Utils
joblib>=1.3.0
tqdm>=4.65.0
python-dotenv>=1.0.0
```

### 단계별 실행

```bash
# Phase 1: LightGBM
python scripts/train_phase1.py

# Phase 2: LSTM (GPU 권장)
python scripts/train_lstm.py

# Phase 3: 전체 파이프라인
python scripts/train_full_pipeline.py
```

## 성능 벤치마크

### 예상 성능 (RTX 3080 기준)

| 작업 | CPU | GPU | 속도 향상 |
|------|-----|-----|----------|
| 데이터 로드 (100만 행) | 10초 | 10초 | 1x |
| 특성 생성 (100만 행) | 60초 | 15초 | 4x |
| LightGBM 학습 | 300초 | 120초 | 2.5x |
| LSTM 학습 (100 epochs) | 3600초 | 300초 | 12x |
| 예측 (10만 행) | 5초 | 1초 | 5x |

## 다음 단계

1. **백테스팅 엔진 통합**
   - 실제 거래 시뮬레이션
   - 수수료 및 슬리피지 고려
   - 리스크 관리 적용

2. **실시간 예측 시스템**
   - FastAPI 기반 예측 서버
   - 웹소켓 실시간 데이터 처리
   - 레이턴시 최적화

3. **모니터링 대시보드**
   - Streamlit 기반 UI
   - 실시간 성과 추적
   - 모델 디버깅 도구
