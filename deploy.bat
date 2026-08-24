@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1" %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] O deploy falhou com o codigo %ERRORLEVEL%.
    if "%~1"=="" pause
    exit /b %ERRORLEVEL%
)
