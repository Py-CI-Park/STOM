@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title STOM - Virtual Environment Setup
cls

echo ============================================================
echo STOM virtual environment setup
echo ============================================================
echo.
echo Current directory: %CD%
echo Script directory : %~dp0
echo.

>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "cmd.exe", "/c ""%~f0""", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B
)

pushd "%CD%"
CD /D "%~dp0"

set PYTHON32_CMD=C:\Python\32\Python3119\python32.exe
set PYTHON64_CMD=C:\Python\64\Python3119\python.exe

echo [1/7] Checking system Python installations...
if not exist "%PYTHON64_CMD%" (
    echo [ERROR] Missing required 64-bit Python:
    echo         %PYTHON64_CMD%
    pause
    exit /b 1
)
"%PYTHON64_CMD%" --version

if not exist "%PYTHON32_CMD%" (
    echo [ERROR] Missing required 32-bit Python:
    echo         %PYTHON32_CMD%
    pause
    exit /b 1
)
"%PYTHON32_CMD%" --version
echo.

echo [2/7] Creating virtual environments...
"%PYTHON64_CMD%" -m venv "%~dp0venv_64bit" --clear
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create venv_64bit.
    pause
    exit /b 1
)

"%PYTHON32_CMD%" -m venv "%~dp0venv_32bit" --clear
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create venv_32bit.
    pause
    exit /b 1
)

if not exist "%~dp0venv_64bit\Scripts\python.exe" (
    echo [ERROR] venv_64bit was not created correctly.
    pause
    exit /b 1
)
if not exist "%~dp0venv_32bit\Scripts\python32.exe" (
    echo [ERROR] venv_32bit was not created correctly.
    pause
    exit /b 1
)
echo.

echo [3/7] Upgrading pip tooling...
"%~dp0venv_64bit\Scripts\python.exe" -m pip install --upgrade pip wheel
if %errorlevel% neq 0 (
    echo [ERROR] Failed to upgrade 64-bit pip tooling.
    pause
    exit /b 1
)
"%~dp0venv_64bit\Scripts\python.exe" -m pip install "setuptools<80"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install 64-bit setuptools.
    pause
    exit /b 1
)

"%~dp0venv_32bit\Scripts\python32.exe" -m pip install --upgrade pip wheel
if %errorlevel% neq 0 (
    echo [ERROR] Failed to upgrade 32-bit pip tooling.
    pause
    exit /b 1
)
"%~dp0venv_32bit\Scripts\python32.exe" -m pip install "setuptools<80"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install 32-bit setuptools.
    pause
    exit /b 1
)
echo.

echo [4/7] Installing 32-bit requirements...
"%~dp0venv_32bit\Scripts\python32.exe" -m pip install -r "%~dp0requirements_32bit.txt"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements_32bit.txt.
    pause
    exit /b 1
)
if not exist "%~dp0utility\TA_Lib-0.4.27-cp311-cp311-win32.whl" (
    echo [ERROR] Missing 32-bit TA-Lib wheel.
    pause
    exit /b 1
)
"%~dp0venv_32bit\Scripts\python32.exe" -m pip install "%~dp0utility\TA_Lib-0.4.27-cp311-cp311-win32.whl"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install 32-bit TA-Lib wheel.
    pause
    exit /b 1
)
echo.

echo [5/7] Installing 64-bit requirements...
"%~dp0venv_64bit\Scripts\python.exe" -m pip install -r "%~dp0requirements_64bit.txt"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements_64bit.txt.
    pause
    exit /b 1
)
if not exist "%~dp0utility\TA_Lib-0.4.25-cp311-cp311-win_amd64.whl" (
    echo [ERROR] Missing 64-bit TA-Lib wheel.
    pause
    exit /b 1
)
"%~dp0venv_64bit\Scripts\python.exe" -m pip install "%~dp0utility\TA_Lib-0.4.25-cp311-cp311-win_amd64.whl"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install 64-bit TA-Lib wheel.
    pause
    exit /b 1
)
echo.

echo [6/7] Verifying environments...
"%~dp0venv_64bit\Scripts\python.exe" -c "import numpy, pandas, PyQt5, PyQt5.QtWebEngineWidgets, zmq, pyttsx3, websockets, cryptography, talib; print('64-bit environment OK')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 64-bit environment import verification failed.
    pause
    exit /b 1
)

"%~dp0venv_32bit\Scripts\python32.exe" -c "import numpy, pandas, PyQt5, zmq, win32api, cryptography, talib; print('32-bit environment OK')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 32-bit environment import verification failed.
    pause
    exit /b 1
)
echo.

echo [7/7] Summary
echo   - 32-bit venv ready: venv_32bit
if exist "%~dp0venv_64bit\Scripts\python.exe" (
    echo   - 64-bit venv ready: venv_64bit
)
echo.
echo Next steps:
echo   1. Default UI   : stom.bat
echo   2. Stock mode   : stom_stock.bat
echo   3. Coin mode    : stom_coin.bat
echo.
echo Setup complete.
pause
endlocal
exit /b 0
