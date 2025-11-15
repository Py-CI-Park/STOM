# 배포 및 운영 가이드

## 1. 시스템 요구사항

### 1.1 하드웨어 요구사항

#### 최소 사양
- **CPU**: Intel i5 또는 AMD Ryzen 5 이상
- **RAM**: 16GB
- **GPU**: NVIDIA GTX 1060 (6GB VRAM)
- **저장공간**: 50GB SSD

#### 권장 사양
- **CPU**: Intel i7/i9 또는 AMD Ryzen 7/9
- **RAM**: 32GB 이상
- **GPU**: NVIDIA RTX 3070 이상 (8GB+ VRAM)
- **저장공간**: 100GB+ NVMe SSD

### 1.2 소프트웨어 요구사항

```yaml
운영체제:
  - Windows 10/11 (64-bit)
  - Ubuntu 20.04/22.04 LTS
  
Python: 3.9 - 3.11

CUDA (GPU 사용시):
  - CUDA Toolkit 11.8+
  - cuDNN 8.6+
  - NVIDIA Driver 520+

데이터베이스:
  - SQLite 3.35+
```

## 2. 환경 설정

### 2.1 Windows 환경 설정

```powershell
# 1. Python 설치 확인
python --version

# 2. CUDA 설치 (GPU 사용시)
# https://developer.nvidia.com/cuda-11-8-0-download-archive 에서 다운로드

# 3. 환경변수 설정
[System.Environment]::SetEnvironmentVariable("CUDA_PATH", "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8", "User")
[System.Environment]::SetEnvironmentVariable("PATH", "$env:PATH;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin", "User")

# 4. Visual Studio Build Tools 설치 (C++ 컴파일러)
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
```

### 2.2 Linux 환경 설정

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. Python 및 필수 패키지 설치
sudo apt install python3.9 python3.9-dev python3.9-venv
sudo apt install build-essential cmake git

# 3. CUDA 설치 (GPU 사용시)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-11-8

# 4. 환경변수 설정
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

## 3. 프로젝트 설치

### 3.1 프로젝트 구조 생성

```bash
# 프로젝트 디렉토리 생성
mkdir stom_ml_optimizer
cd stom_ml_optimizer

# 디렉토리 구조 생성
mkdir -p {core,data,models,training,backtesting,api,scripts,configs,logs,cache,reports}
mkdir -p data/{raw,processed,features}
mkdir -p models/{saved,checkpoints}
```

### 3.2 가상환경 설정 및 패키지 설치

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip setuptools wheel

# 기본 패키지 설치
pip install -r requirements.txt

# GPU 패키지 설치 (선택사항)
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118
pip install cupy-cuda118
```

### 3.3 requirements.txt

```txt
# Core Dependencies
pandas==1.5.3
numpy==1.24.3
scikit-learn==1.3.0
scipy==1.11.1

# Machine Learning
lightgbm==4.0.0
xgboost==1.7.6
optuna==3.3.0
catboost==1.2

# Deep Learning (CPU version)
torch==2.0.1
torchvision==0.15.2

# Technical Analysis
ta-lib==0.4.27
pandas-ta==0.3.14b0

# Database
sqlalchemy==2.0.19
sqlite3

# API & Web
fastapi==0.100.0
uvicorn[standard]==0.23.1
pydantic==2.1.1
python-multipart==0.0.6

# Visualization
matplotlib==3.7.2
seaborn==0.12.2
plotly==5.15.0
streamlit==1.25.0

# Utilities
joblib==1.3.1
tqdm==4.65.0
python-dotenv==1.0.0
pyyaml==6.0.1
loguru==0.7.0

# Development
pytest==7.4.0
pytest-cov==4.1.0
black==23.7.0
flake8==6.0.0
mypy==1.4.1
```

### 3.4 TA-Lib 설치 (Windows)

```powershell
# TA-Lib 바이너리 다운로드 및 설치
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib 에서 
# Python 버전에 맞는 whl 파일 다운로드

# 예: Python 3.9 64-bit
pip install TA_Lib-0.4.27-cp39-cp39-win_amd64.whl
```

## 4. 설정 파일

### 4.1 프로젝트 설정 (configs/config.yaml)

```yaml
# configs/config.yaml
project:
  name: "STOM ML Optimizer"
  version: "1.0.0"
  environment: "development"  # development, staging, production

database:
  path: "./data/stock_data.db"
  cache_size: 100000
  
data_pipeline:
  cache_dir: "./cache"
  use_cache: true
  max_workers: 4
  
models:
  save_dir: "./models/saved"
  checkpoint_dir: "./models/checkpoints"
  
  lightgbm:
    n_trials: 50
    cv_folds: 5
    early_stopping_rounds: 100
    
  lstm:
    batch_size: 64
    epochs: 100
    learning_rate: 0.001
    early_stopping_patience: 10
    
backtesting:
  initial_capital: 10000000
  max_positions: 10
  position_size: 0.1
  stop_loss: -3.0
  take_profit: 5.0
  trailing_stop: 2.0
  commission: 0.00015
  tax: 0.0023
  
api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: false
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/app.log"
  max_size: "10MB"
  backup_count: 5
```

### 4.2 환경변수 설정 (.env)

```bash
# .env
# API Keys (if needed)
OPENAI_API_KEY=your_api_key_here
ALPHA_VANTAGE_KEY=your_api_key_here

# Database
DB_PATH=./data/stock_data.db

# Model Settings
MODEL_PATH=./models/saved
CHECKPOINT_PATH=./models/checkpoints

# Server Settings
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

## 5. 실행 스크립트

### 5.1 전체 파이프라인 실행 (run.py)

```python
#!/usr/bin/env python
# run.py
import os
import sys
import yaml
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent))

def setup_logging(config):
    """로깅 설정"""
    logging.basicConfig(
        level=config['logging']['level'],
        format=config['logging']['format'],
        handlers=[
            logging.FileHandler(config['logging']['file']),
            logging.StreamHandler()
        ]
    )

def load_config(config_path='configs/config.yaml'):
    """설정 파일 로드"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description='STOM ML Optimizer')
    parser.add_argument('command', choices=['train', 'backtest', 'predict', 'api', 'dashboard'])
    parser.add_argument('--config', default='configs/config.yaml', help='Config file path')
    parser.add_argument('--model', default='lightgbm', choices=['lightgbm', 'lstm', 'ensemble'])
    parser.add_argument('--stocks', nargs='+', default=['005930', '000660'])
    parser.add_argument('--start-date', default='20220101000000')
    parser.add_argument('--end-date', default='20231231235959')
    
    args = parser.parse_args()
    
    # 설정 로드
    config = load_config(args.config)
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {args.command} command...")
    
    if args.command == 'train':
        from scripts.train_full_pipeline import main as train_main
        train_main()
        
    elif args.command == 'backtest':
        from scripts.run_backtest import main as backtest_main
        backtest_main()
        
    elif args.command == 'predict':
        from api.predictor import predict_batch
        predictions = predict_batch(args.stocks, args.model)
        print(predictions)
        
    elif args.command == 'api':
        import uvicorn
        uvicorn.run(
            "api.server:app",
            host=config['api']['host'],
            port=config['api']['port'],
            workers=config['api']['workers'],
            reload=config['api']['reload']
        )
        
    elif args.command == 'dashboard':
        import streamlit.cli as stcli
        stcli.main(['run', 'dashboard/app.py'])

if __name__ == "__main__":
    main()
```

### 5.2 배치 실행 스크립트

#### Windows (run.bat)
```batch
@echo off
echo ========================================
echo STOM ML Optimizer
echo ========================================

:: 가상환경 활성화
call venv\Scripts\activate

:: 명령 실행
if "%1"=="train" (
    echo Training models...
    python run.py train --model %2
) else if "%1"=="backtest" (
    echo Running backtest...
    python run.py backtest
) else if "%1"=="api" (
    echo Starting API server...
    python run.py api
) else if "%1"=="dashboard" (
    echo Starting dashboard...
    python run.py dashboard
) else (
    echo Usage: run.bat [train^|backtest^|api^|dashboard] [options]
)

pause
```

#### Linux (run.sh)
```bash
#!/bin/bash

echo "========================================"
echo "STOM ML Optimizer"
echo "========================================"

# 가상환경 활성화
source venv/bin/activate

# 명령 실행
case "$1" in
    train)
        echo "Training models..."
        python run.py train --model ${2:-lightgbm}
        ;;
    backtest)
        echo "Running backtest..."
        python run.py backtest
        ;;
    api)
        echo "Starting API server..."
        python run.py api
        ;;
    dashboard)
        echo "Starting dashboard..."
        python run.py dashboard
        ;;
    *)
        echo "Usage: ./run.sh {train|backtest|api|dashboard} [options]"
        exit 1
esac
```

## 6. API 서버

### 6.1 FastAPI 서버 (api/server.py)

```python
# api/server.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

app = FastAPI(title="STOM ML Optimizer API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionRequest(BaseModel):
    stock_codes: List[str]
    model_type: str = "lightgbm"
    lookback_period: int = 100

class PredictionResponse(BaseModel):
    stock_code: str
    prediction: float
    signal: str
    confidence: float
    timestamp: str

@app.get("/")
def root():
    return {"message": "STOM ML Optimizer API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/predict", response_model=List[PredictionResponse])
async def predict(request: PredictionRequest):
    """실시간 예측 API"""
    try:
        from api.predictor import get_predictions
        
        predictions = get_predictions(
            request.stock_codes,
            request.model_type,
            request.lookback_period
        )
        
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest")
async def run_backtest(background_tasks: BackgroundTasks):
    """백테스팅 실행 (비동기)"""
    background_tasks.add_task(execute_backtest)
    return {"message": "Backtest started", "status": "running"}

@app.get("/models")
def list_models():
    """사용 가능한 모델 목록"""
    return {
        "models": ["lightgbm", "lstm", "xgboost", "ensemble"],
        "default": "lightgbm"
    }

@app.get("/performance")
def get_performance():
    """최근 성과 지표"""
    # 실제 구현 필요
    return {
        "total_return": 15.3,
        "sharpe_ratio": 1.8,
        "max_drawdown": -5.2,
        "win_rate": 0.62
    }

def execute_backtest():
    """백테스팅 실행 함수"""
    import subprocess
    subprocess.run(["python", "scripts/run_backtest.py"])
```

## 7. 모니터링 대시보드

### 7.1 Streamlit 대시보드 (dashboard/app.py)

```python
# dashboard/app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time

st.set_page_config(
    page_title="STOM ML Optimizer Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 STOM ML/DL 백테스팅 최적화 시스템")

# 사이드바
with st.sidebar:
    st.header("설정")
    
    model_type = st.selectbox(
        "모델 선택",
        ["lightgbm", "lstm", "xgboost", "ensemble"]
    )
    
    stock_codes = st.multiselect(
        "종목 선택",
        ["005930", "000660", "035720", "051910"],
        default=["005930", "000660"]
    )
    
    if st.button("예측 실행"):
        with st.spinner("예측 중..."):
            # API 호출
            response = requests.post(
                "http://localhost:8000/predict",
                json={
                    "stock_codes": stock_codes,
                    "model_type": model_type
                }
            )
            if response.status_code == 200:
                st.success("예측 완료!")
            else:
                st.error("예측 실패")

# 메인 대시보드
tab1, tab2, tab3, tab4 = st.tabs(["📊 실시간", "📈 백테스팅", "🎯 모델 성능", "⚙️ 설정"])

with tab1:
    st.header("실시간 예측")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 수익률", "15.3%", "2.1%")
    with col2:
        st.metric("샤프 비율", "1.85", "0.12")
    with col3:
        st.metric("최대 낙폭", "-5.2%", "-0.3%")
    with col4:
        st.metric("승률", "62%", "3%")
    
    # 실시간 차트
    st.subheader("포트폴리오 가치")
    
    # 더미 데이터 (실제로는 API에서 가져옴)
    import numpy as np
    
    dates = pd.date_range(start='2023-01-01', periods=180, freq='D')
    portfolio_value = 10000000 * (1 + np.random.randn(180).cumsum() * 0.01)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=portfolio_value,
        mode='lines',
        name='Portfolio Value',
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Portfolio Value (KRW)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("백테스팅 결과")
    
    # 백테스팅 설정
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("시작일", pd.to_datetime("2023-01-01"))
    with col2:
        end_date = st.date_input("종료일", pd.to_datetime("2023-12-31"))
    with col3:
        initial_capital = st.number_input("초기 자본", value=10000000, step=1000000)
    
    if st.button("백테스팅 실행"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            progress_bar.progress(i + 1)
            status_text.text(f'진행률: {i+1}%')
            time.sleep(0.01)
        
        st.success("백테스팅 완료!")
        
        # 결과 표시
        results = {
            "총 거래": 245,
            "승리": 152,
            "패배": 93,
            "승률": "62%",
            "평균 수익": "2.3%",
            "평균 손실": "-1.5%",
            "Profit Factor": 1.85
        }
        
        st.json(results)

with tab3:
    st.header("모델 성능 비교")
    
    # 모델별 성능 비교
    models_performance = pd.DataFrame({
        'Model': ['LightGBM', 'LSTM', 'XGBoost', 'Ensemble'],
        'Accuracy': [0.65, 0.62, 0.64, 0.68],
        'Precision': [0.67, 0.63, 0.65, 0.69],
        'Recall': [0.63, 0.61, 0.63, 0.67],
        'F1 Score': [0.65, 0.62, 0.64, 0.68]
    })
    
    fig = go.Figure()
    
    for metric in ['Accuracy', 'Precision', 'Recall', 'F1 Score']:
        fig.add_trace(go.Bar(
            name=metric,
            x=models_performance['Model'],
            y=models_performance[metric]
        ))
    
    fig.update_layout(
        barmode='group',
        height=400,
        title="모델별 성능 지표"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 특성 중요도
    st.subheader("특성 중요도 (Top 10)")
    
    feature_importance = pd.DataFrame({
        'Feature': ['초당거래대금', '체결강도', '등락율', '매도총잔량', '매수총잔량',
                   'RSI', 'MACD', '이동평균', '볼린저밴드', '거래량'],
        'Importance': [0.15, 0.12, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
    })
    
    fig = go.Figure(go.Bar(
        x=feature_importance['Importance'],
        y=feature_importance['Feature'],
        orientation='h'
    ))
    
    fig.update_layout(
        height=400,
        title="특성 중요도",
        xaxis_title="Importance",
        yaxis_title="Feature"
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("시스템 설정")
    
    st.subheader("데이터베이스")
    db_path = st.text_input("DB 경로", value="./data/stock_data.db")
    
    st.subheader("모델 설정")
    col1, col2 = st.columns(2)
    
    with col1:
        epochs = st.slider("Epochs", 10, 200, 100)
        batch_size = st.slider("Batch Size", 16, 128, 64)
    
    with col2:
        learning_rate = st.slider("Learning Rate", 0.0001, 0.1, 0.001, format="%.4f")
        dropout = st.slider("Dropout", 0.0, 0.5, 0.2)
    
    st.subheader("백테스팅 설정")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        stop_loss = st.slider("Stop Loss (%)", -10.0, -1.0, -3.0)
    with col2:
        take_profit = st.slider("Take Profit (%)", 1.0, 20.0, 5.0)
    with col3:
        position_size = st.slider("Position Size (%)", 5, 30, 10)
    
    if st.button("설정 저장"):
        st.success("설정이 저장되었습니다!")
```

## 8. 시스템 모니터링

### 8.1 로그 모니터링

```python
# monitoring/log_monitor.py
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import sys

def setup_monitoring():
    """모니터링 설정"""
    
    # 로거 생성
    logger = logging.getLogger('stom_ml')
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러 (로테이션)
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s - %(message)s')
    )
    
    # 이메일 알림 (에러 발생시)
    if False:  # 필요시 활성화
        mail_handler = SMTPHandler(
            mailhost='smtp.gmail.com',
            fromaddr='alert@stom.com',
            toaddrs=['admin@stom.com'],
            subject='STOM ML System Error',
            credentials=('username', 'password'),
            secure=()
        )
        mail_handler.setLevel(logging.ERROR)
        logger.addHandler(mail_handler)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

### 8.2 성능 모니터링

```python
# monitoring/performance_monitor.py
import psutil
import GPUtil
import time
from datetime import datetime

class SystemMonitor:
    """시스템 리소스 모니터링"""
    
    @staticmethod
    def get_system_info():
        """시스템 정보 수집"""
        
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # GPU 정보 (NVIDIA)
        gpu_info = []
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_info.append({
                    'name': gpu.name,
                    'load': f"{gpu.load*100:.1f}%",
                    'memory': f"{gpu.memoryUsed}/{gpu.memoryTotal}MB",
                    'temp': f"{gpu.temperature}°C"
                })
        except:
            gpu_info = None
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_used_gb': memory_used_gb,
            'disk_percent': disk_percent,
            'gpu_info': gpu_info
        }
    
    @staticmethod
    def monitor_loop(interval=60):
        """모니터링 루프"""
        while True:
            info = SystemMonitor.get_system_info()
            
            # 로그 기록
            with open('logs/system_monitor.log', 'a') as f:
                f.write(f"{info}\n")
            
            # 경고 확인
            if info['cpu_percent'] > 90:
                print(f"⚠️ CPU 사용률 높음: {info['cpu_percent']}%")
            
            if info['memory_percent'] > 90:
                print(f"⚠️ 메모리 사용률 높음: {info['memory_percent']}%")
            
            time.sleep(interval)
```

## 9. 운영 및 유지보수

### 9.1 일일 점검 스크립트

```python
# scripts/daily_check.py
#!/usr/bin/env python

import os
import sys
import sqlite3
from datetime import datetime, timedelta
import logging

def check_database():
    """데이터베이스 상태 확인"""
    try:
        conn = sqlite3.connect('./data/stock_data.db')
        cursor = conn.cursor()
        
        # 테이블 수 확인
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        # 최신 데이터 확인
        cursor.execute("SELECT MAX(datetime('now')) FROM '005930' LIMIT 1")
        latest_data = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'status': 'OK',
            'tables': table_count,
            'latest_data': latest_data
        }
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e)}

def check_models():
    """모델 상태 확인"""
    model_files = [
        './models/saved/lightgbm_model.pkl',
        './models/saved/lstm_model.pth',
        './models/saved/ensemble_model.pkl'
    ]
    
    results = {}
    for model_file in model_files:
        if os.path.exists(model_file):
            size = os.path.getsize(model_file) / (1024*1024)  # MB
            modified = datetime.fromtimestamp(os.path.getmtime(model_file))
            results[model_file] = {
                'exists': True,
                'size_mb': f"{size:.2f}",
                'modified': modified.isoformat()
            }
        else:
            results[model_file] = {'exists': False}
    
    return results

def check_disk_space():
    """디스크 공간 확인"""
    import shutil
    
    total, used, free = shutil.disk_usage("/")
    
    return {
        'total_gb': total // (2**30),
        'used_gb': used // (2**30),
        'free_gb': free // (2**30),
        'used_percent': (used / total) * 100
    }

def main():
    print("=" * 60)
    print("일일 시스템 점검")
    print("=" * 60)
    print(f"점검 시간: {datetime.now()}")
    print()
    
    # 데이터베이스 점검
    print("1. 데이터베이스 점검")
    db_status = check_database()
    for key, value in db_status.items():
        print(f"  - {key}: {value}")
    print()
    
    # 모델 점검
    print("2. 모델 파일 점검")
    model_status = check_models()
    for model, status in model_status.items():
        print(f"  - {model}:")
        for key, value in status.items():
            print(f"    {key}: {value}")
    print()
    
    # 디스크 공간 점검
    print("3. 디스크 공간")
    disk_status = check_disk_space()
    for key, value in disk_status.items():
        print(f"  - {key}: {value}")
    
    # 경고 확인
    if disk_status['used_percent'] > 80:
        print("\n⚠️ 경고: 디스크 사용률이 80%를 초과했습니다!")
    
    print("\n점검 완료!")

if __name__ == "__main__":
    main()
```

### 9.2 백업 스크립트

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backup/stom_ml"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting backup at $DATE"

# 데이터베이스 백업
mkdir -p $BACKUP_DIR/db
cp ./data/stock_data.db $BACKUP_DIR/db/stock_data_$DATE.db

# 모델 백업
mkdir -p $BACKUP_DIR/models
cp -r ./models/saved/* $BACKUP_DIR/models/

# 설정 파일 백업
mkdir -p $BACKUP_DIR/configs
cp -r ./configs/* $BACKUP_DIR/configs/

# 압축
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/db $BACKUP_DIR/models $BACKUP_DIR/configs

# 30일 이상 된 백업 삭제
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed"
```

## 10. 문제 해결

### 10.1 자주 발생하는 문제

#### CUDA 메모리 부족
```python
# GPU 메모리 정리
import torch
torch.cuda.empty_cache()

# 배치 크기 줄이기
batch_size = 32  # 64에서 감소
```

#### TA-Lib 설치 오류
```bash
# Windows: Visual C++ 14.0 필요
# https://visualstudio.microsoft.com/downloads/

# Linux
sudo apt-get install ta-lib
pip install ta-lib
```

#### 데이터베이스 락
```python
# 타임아웃 증가
conn = sqlite3.connect('stock_data.db', timeout=30.0)
```

### 10.2 성능 최적화 팁

1. **데이터 캐싱 활용**
2. **배치 처리 크기 조정**
3. **불필요한 특성 제거**
4. **모델 경량화 (pruning, quantization)**
5. **비동기 처리 활용**

## 11. 결론

이 가이드를 통해 STOM ML/DL 백테스팅 최적화 시스템을 성공적으로 배포하고 운영할 수 있습니다. 지속적인 모니터링과 개선을 통해 시스템 성능을 최적화하세요.
