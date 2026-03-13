@echo off
chcp 65001 >nul
title STOM (Virtual Environment)

set VENV_32BIT=%~dp0venv_32bit
set VENV_64BIT=%~dp0venv_64bit
set PYTHON_32BIT=%VENV_32BIT%\Scripts\python32.exe
set PYTHON_64BIT=%VENV_64BIT%\Scripts\python.exe

if not exist "%PYTHON_64BIT%" (
    echo [ERROR] 64-bit virtual environment is missing.
    echo [INFO] Run setup_stom.bat first.
    pause
    exit /b 1
)

if not exist "%PYTHON_32BIT%" (
    echo [ERROR] 32-bit virtual environment is missing.
    echo [INFO] STOM requires venv_32bit. Run setup_stom.bat first.
    pause
    exit /b 1
)

>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"=""
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
    cls
    echo ============================================
    echo   SSSSS  TTTTT  OOOOO  M   M
    echo  SS        T   OO   OO MM MM
    echo   SSS      T   OO   OO M M M
    echo     SS     T   OO   OO M   M
    echo  SSSSS     T    OOOOO  M   M
    echo ============================================
    echo   STOM Default Launcher
    echo ============================================
    echo.

    "%PYTHON_64BIT%" -c "import PyQt5, PyQt5.QtWebEngineWidgets, zmq, pyttsx3, websockets, cryptography, talib" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] 64-bit virtual environment is incomplete.
        echo [INFO] Run setup_stom.bat again.
        pause
        exit /b 1
    )

    "%PYTHON_32BIT%" -c "import PyQt5, zmq, win32api, cryptography, talib" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] 32-bit virtual environment is incomplete.
        echo [INFO] Run setup_stom.bat again.
        pause
        exit /b 1
    )

    "%PYTHON_64BIT%" ./utility/database_check.py
    if %errorlevel% neq 0 (
        echo [ERROR] Database check failed.
        pause
        exit /b 1
    )

    "%PYTHON_64BIT%" stom.py %*
    pause
