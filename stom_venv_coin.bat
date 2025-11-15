@echo off
chcp 65001 >nul
title STOM V1 - Crypto Trading (Virtual Environment)

REM ============================================
REM STOM V1 - 암호화폐 트레이딩 (가상환경 모드)
REM ============================================

set VENV_64BIT=%~dp0venv_64bit
set PYTHON_64BIT=%VENV_64BIT%\Scripts\python.exe

if not exist "%PYTHON_64BIT%" (
    echo [오류] 64비트 가상환경이 없습니다
    echo [안내] scripts\setup_venv.bat를 먼저 실행하세요.
    echo.
    pause
    exit /b 1
)

REM UAC 권한 상승
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

    echo ========================================
    echo STOM V1 - Cryptocurrency Trading (가상환경)
    echo ========================================
    echo 64-bit Python: %PYTHON_64BIT%
    echo.

    echo [1/2] 데이터베이스 검증 중...
    "%PYTHON_64BIT%" ./utility/database_check.py
    if %errorlevel% neq 0 (
        echo [오류] 데이터베이스 검증 실패
        pause
        exit /b 1
    )
    echo [완료] 데이터베이스 정상
    echo.

    echo [2/2] STOM V1 - Coin Mode 실행 중...
    "%PYTHON_64BIT%" stom.py coin

    if %errorlevel% neq 0 (
        echo.
        echo [오류] STOM 실행 중 오류 발생
    )

    pause
