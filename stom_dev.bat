@echo off
REM STOM 개발자 모드 - .pyc 캐시 자동 삭제

>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"=""
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"

    REM 개발 모드 활성화
    set STOM_DEV_MODE=1

    echo ================================
    echo STOM 개발자 모드 시작
    echo .pyc 캐시 자동 삭제 활성화
    echo ================================
    echo.

    python ./utility/database_check.py
    python stom.py
    pause
