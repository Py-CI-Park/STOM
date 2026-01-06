@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title "STOM V1 - 가상환경 설정 및 의존성 설치"
cls

REM ============================================
REM 디버깅 및 에러 방지 설정
REM ============================================
echo ============================================================
echo STOM V1 가상환경 설정 시작
echo ============================================================
echo.
echo 현재 디렉토리: %CD%
echo 배치파일 위치: %~dp0
echo 실행 시간: %TIME%
echo.

REM ============================================
REM 관리자 권한 확인
REM ============================================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

if '%errorlevel%' NEQ '0' (
    echo ============================================================
    echo 관리자 권한이 필요합니다.
    echo 관리자 권한으로 다시 실행합니다...
    echo ============================================================
    echo.

    REM UAC 프롬프트를 위한 VBS 스크립트 생성
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "cmd.exe", "/c ""%~f0""", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B
) else (
    goto :gotAdmin
)

:gotAdmin
pushd "%CD%"
CD /D "%~dp0"

echo ============================================================
echo STOM V1 가상환경 설정 및 의존성 설치
echo ============================================================
echo.
echo [정보] 관리자 권한으로 실행 중입니다.
echo [정보] 작업 디렉토리: %CD%
echo.

REM ============================================
REM 1단계: Python 설치 확인
REM ============================================
echo [1/7] Python 설치 확인 중...
echo ----------------------------------------
echo.

REM Python 32비트 및 64비트 경로 지정
set PYTHON32_CMD=C:\Python\32\Python3119\python32.exe
set PYTHON64_CMD=C:\Python\64\Python3119\python.exe

echo Python 32비트 확인 중...
if exist "%PYTHON32_CMD%" (
    echo   [성공] Python 32비트 발견: %PYTHON32_CMD%
    "%PYTHON32_CMD%" --version
) else (
    echo   [경고] Python 32비트를 찾을 수 없습니다: %PYTHON32_CMD%
    echo   32비트 가상환경 생성을 건너뜁니다.
)

echo.
echo Python 64비트 확인 중...
if exist "%PYTHON64_CMD%" (
    echo   [성공] Python 64비트 발견: %PYTHON64_CMD%
    "%PYTHON64_CMD%" --version
) else (
    echo ============================================================
    echo [오류] Python 64비트를 찾을 수 없습니다!
    echo ============================================================
    echo.
    echo 경로: %PYTHON64_CMD%
    echo.
    echo Python 64비트가 위 경로에 설치되어 있어야 합니다.
    echo 설치 후 다시 실행해주세요.
    echo.
    pause
    exit /b 1
)

REM Python 아키텍처 확인
echo.
echo Python 아키텍처 확인:
if exist "%PYTHON32_CMD%" (
    echo 32비트 Python:
    "%PYTHON32_CMD%" -c "import sys, platform; print(f'  Platform: {platform.platform()}'); print(f'  Machine: {platform.machine()}'); print(f'  32-bit: {sys.maxsize <= 2**32}'); print(f'  Executable: {sys.executable}')" 2>nul
    echo.
)
if exist "%PYTHON64_CMD%" (
    echo 64비트 Python:
    "%PYTHON64_CMD%" -c "import sys, platform; print(f'  Platform: {platform.platform()}'); print(f'  Machine: {platform.machine()}'); print(f'  64-bit: {sys.maxsize > 2**32}'); print(f'  Executable: {sys.executable}')" 2>nul
    echo.
)

echo.
echo [완료] Python 확인 완료
echo.

REM ============================================
REM 2단계: 가상환경 생성
REM ============================================
echo [2/7] 가상환경 생성 중...
echo ----------------------------------------
echo.

REM 기존 가상환경 확인
if exist "%~dp0venv_32bit" (
    echo [정보] 기존 venv_32bit 폴더가 존재합니다. 재생성합니다.
)
if exist "%~dp0venv_64bit" (
    echo [정보] 기존 venv_64bit 폴더가 존재합니다. 재생성합니다.
)
echo.

REM 32비트 가상환경 생성 시도 (선택사항)
if exist "%PYTHON32_CMD%" (
    echo 32비트 가상환경 생성 중...
    "%PYTHON32_CMD%" -m venv "%~dp0venv_32bit" --clear
    if %errorlevel% neq 0 (
        echo [경고] 32비트 가상환경 생성 실패
        echo.
    ) else (
        echo [성공] venv_32bit 생성 완료
        echo.
    )
) else (
    echo [정보] Python 32비트가 없어 32비트 가상환경 생성을 건너뜁니다.
    echo.
)

REM 64비트 가상환경 생성 (필수)
echo 64비트 가상환경 생성 중...
"%PYTHON64_CMD%" -m venv "%~dp0venv_64bit" --clear
if %errorlevel% neq 0 (
    echo [오류] 64비트 가상환경 생성 실패
    echo 오류 코드: %errorlevel%
    echo.
    echo Python venv 모듈 확인:
    "%PYTHON64_CMD%" -m venv --help
    echo.
    pause
    exit /b 1
) else (
    echo [성공] venv_64bit 생성 완료
    echo.
)

REM 가상환경 생성 확인 (python.exe로 생성됨)
if not exist "%~dp0venv_64bit\Scripts\python.exe" (
    echo ============================================================
    echo [오류] 가상환경을 생성할 수 없습니다!
    echo ============================================================
    echo.
    echo 가능한 원인:
    echo   - Python venv 모듈이 설치되지 않음
    echo   - 디스크 공간 부족
    echo   - 권한 문제
    echo.
    echo 생성된 파일 확인:
    dir "%~dp0venv_64bit\Scripts\" 2>nul
    echo.
    pause
    exit /b 1
)

echo [완료] 가상환경 생성 단계 완료
echo.

REM ============================================
REM 3단계: pip 업그레이드
REM ============================================
echo [3/7] pip 업그레이드 중...
echo ----------------------------------------
echo.

if exist "%~dp0venv_32bit\Scripts\python32.exe" (
    echo 32비트 환경 pip 업그레이드...
    "%~dp0venv_32bit\Scripts\python32.exe" -m pip install --upgrade pip setuptools wheel
    echo.
)

if exist "%~dp0venv_64bit\Scripts\python.exe" (
    echo 64비트 환경 pip 업그레이드...
    "%~dp0venv_64bit\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
    echo.
)

echo [완료] pip 업그레이드 단계 완료
echo.

REM ============================================
REM 4단계: 32비트 환경 의존성 설치
REM ============================================
if exist "%~dp0venv_32bit\Scripts\python32.exe" (
    echo [4/7] 32비트 환경 의존성 설치 중...
    echo ----------------------------------------
    echo.

    echo 기본 패키지 설치 중...
    "%~dp0venv_32bit\Scripts\python32.exe" -m pip install numpy==1.26.4 pandas==2.0.3 python-telegram-bot==13.15

    echo 시스템 패키지 설치 중...
    "%~dp0venv_32bit\Scripts\python32.exe" -m pip install psutil pyqt5 pyzmq pywin32 cryptography

    echo TA-Lib 설치 확인 중...
    if exist "%~dp0utility\TA_Lib-0.4.27-cp311-cp311-win32.whl" (
        echo TA-Lib 휠 파일 발견, 설치 중...
        "%~dp0venv_32bit\Scripts\python32.exe" -m pip install "%~dp0utility\TA_Lib-0.4.27-cp311-cp311-win32.whl"
    ) else (
        echo [정보] TA-Lib 32비트 휠 파일이 없습니다.
    )

    echo.
    echo [완료] 32비트 환경 설치 완료
    echo.
) else (
    echo [4/7] 32비트 가상환경이 없어 건너뜁니다.
    echo.
)

REM ============================================
REM 5단계: 64비트 환경 의존성 설치
REM ============================================
echo [5/7] 64비트 환경 의존성 설치 중...
echo ----------------------------------------
echo.

echo 기본 패키지 설치 중...
"%~dp0venv_64bit\Scripts\python.exe" -m pip install numpy==1.26.4 pandas==2.0.3 python-telegram-bot==13.15 numba

echo 웹/시스템 패키지 설치 중...
"%~dp0venv_64bit\Scripts\python.exe" -m pip install websockets cryptography psutil pyqt5 PyQtWebEngine BeautifulSoup4

echo 최적화 패키지 설치 중...
"%~dp0venv_64bit\Scripts\python.exe" -m pip install optuna optuna-dashboard cmaes

echo 머신러닝/통계 패키지 설치 중...
"%~dp0venv_64bit\Scripts\python.exe" -m pip install scikit-learn scipy joblib shap==0.46.0

echo 시각화 패키지 설치 중...
"%~dp0venv_64bit\Scripts\python.exe" -m pip install lxml squarify matplotlib pyqtgraph

echo 트레이딩 API 설치 중...
"%~dp0venv_64bit\Scripts\python.exe" -m pip install pyupbit ntplib python-dateutil python-binance pyzmq pyttsx3

echo TA-Lib 설치 확인 중...
if exist "%~dp0utility\TA_Lib-0.4.25-cp311-cp311-win_amd64.whl" (
    echo TA-Lib 휠 파일 발견, 설치 중...
    "%~dp0venv_64bit\Scripts\python.exe" -m pip install "%~dp0utility\TA_Lib-0.4.25-cp311-cp311-win_amd64.whl"
) else if exist "%~dp0utility\TA_Lib-0.4.27-cp311-cp311-win_amd64.whl" (
    echo TA-Lib 휠 파일 발견, 설치 중...
    "%~dp0venv_64bit\Scripts\python.exe" -m pip install "%~dp0utility\TA_Lib-0.4.27-cp311-cp311-win_amd64.whl"
) else (
    echo [정보] TA-Lib 64비트 휠 파일이 없습니다.
)
echo.
echo [완료] 64비트 환경 설치 완료
echo.

REM ============================================
REM 6단계: 환경 검증
REM ============================================
echo [6/7] 환경 검증 중...
echo ----------------------------------------
echo.

echo 가상환경 존재 확인:
if exist "%~dp0venv_32bit\Scripts\python32.exe" (
    echo   [OK] 32비트 가상환경 존재
) else (
    echo   [--] 32비트 가상환경 없음
)

if exist "%~dp0venv_64bit\Scripts\python.exe" (
    echo   [OK] 64비트 가상환경 존재
) else (
    echo   [!!] 64비트 가상환경 없음 - 오류!
)
echo.

echo Python 아키텍처 검증:
if exist "%~dp0venv_32bit\Scripts\python32.exe" (
    "%~dp0venv_32bit\Scripts\python32.exe" -c "import sys; arch='32-bit' if sys.maxsize <= 2**32 else '64-bit'; print(f'  32비트 환경: {arch}')"
)

if exist "%~dp0venv_64bit\Scripts\python.exe" (
    "%~dp0venv_64bit\Scripts\python.exe" -c "import sys; arch='64-bit' if sys.maxsize > 2**32 else '32-bit'; print(f'  64비트 환경: {arch}')"
)
echo.

echo 필수 패키지 테스트:
if exist "%~dp0venv_32bit\Scripts\python32.exe" (
    "%~dp0venv_32bit\Scripts\python32.exe" -c "import numpy, pandas; print('  [OK] 32비트 핵심 패키지')" 2>nul
    if %errorlevel% neq 0 (
        echo   [경고] 32비트 패키지 설치 실패
    )
)

if exist "%~dp0venv_64bit\Scripts\python.exe" (
    "%~dp0venv_64bit\Scripts\python.exe" -c "import numpy, pandas; print('  [OK] 64비트 핵심 패키지')" 2>nul
    if %errorlevel% neq 0 (
        echo   [경고] 64비트 패키지 설치 실패
    )
)
echo.

echo [완료] 환경 검증 완료
echo.

REM ============================================
REM 7단계: 최종 정보
REM ============================================
echo [7/7] 설치 요약
echo ----------------------------------------
echo.

if exist "%~dp0venv_32bit\Scripts\python32.exe" (
    echo 32비트 환경:
    "%~dp0venv_32bit\Scripts\python32.exe" -c "import sys; print(f'  Python: {sys.version.split()[0]}')"
    "%~dp0venv_32bit\Scripts\python32.exe" -c "import pkg_resources; print(f'  패키지: {len(list(pkg_resources.working_set))}개')"
    echo.
)

if exist "%~dp0venv_64bit\Scripts\python.exe" (
    echo 64비트 환경:
    "%~dp0venv_64bit\Scripts\python.exe" -c "import sys; print(f'  Python: {sys.version.split()[0]}')"
    "%~dp0venv_64bit\Scripts\python.exe" -c "import pkg_resources; print(f'  패키지: {len(list(pkg_resources.working_set))}개')"
    echo.
)

REM ============================================
REM 최종 안내
REM ============================================
echo ============================================================
echo STOM V1 가상환경 설정 완료!
echo ============================================================
echo.
echo [사용된 Python 경로]
if exist "%PYTHON32_CMD%" echo   - 32비트: %PYTHON32_CMD%
if exist "%PYTHON64_CMD%" echo   - 64비트: %PYTHON64_CMD%
echo.
echo [설치된 가상환경]
if exist "%~dp0venv_32bit\Scripts\python32.exe" echo   - 32비트: venv_32bit (Kiwoom API용)
if exist "%~dp0venv_64bit\Scripts\python.exe" echo   - 64비트: venv_64bit (메인 시스템)
echo.
echo [가상환경 모드 감지]
if exist "%~dp0venv_64bit\Scripts\python.exe" (
    "%~dp0venv_64bit\Scripts\python.exe" -c "import os, sys; sys.path.insert(0, '%~dp0'); from utility.setting import VENV_MODE; print(f'  VENV_MODE: {VENV_MODE}')" 2>nul
    if %errorlevel% neq 0 (
        echo   VENV_MODE 확인 불가 - 설정 파일을 확인하세요
    )
) else (
    echo   가상환경이 생성되지 않았습니다.
)
echo.
echo [다음 단계]
echo   1. 주식: stom_venv_stock.bat 실행
echo   2. 코인: stom_venv_coin.bat 실행
echo   3. 기본: stom_venv.bat 실행
echo.
echo [문제 해결]
echo   - 오류 발생 시 이 로그를 확인하세요
echo   - Python 3.11 권장
echo   - 관리자 권한 필요
echo.
echo ============================================================
echo.
echo 아무 키나 누르면 종료합니다...
pause >nul
endlocal
exit /b 0