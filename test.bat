@echo off
chcp 65001 >nul
title Noark 5 Workflow Manager - Tester

echo.
echo ========================================
echo   Noark 5 Workflow Manager - Tester
echo ========================================
echo.

py tests\run_tests.py
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE% equ 0 (
    echo [OK] Alle tester bestått.
) else (
    echo [FEIL] En eller flere tester feilet.
)

echo.
pause
exit /b %EXITCODE%
