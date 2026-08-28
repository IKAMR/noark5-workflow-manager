@echo off
chcp 65001 >nul
title Noark 5 Workflow Manager - Tester
mode con: cols=140 lines=45

if exist "docs\test-results\.last-test-summary.txt" del /q "docs\test-results\.last-test-summary.txt" >nul 2>&1

echo.
echo ========================================
echo   Noark 5 Workflow Manager - Tester
echo ========================================
echo.

py tests\run_tests.py
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
    echo [OK] Alle tester bestatt.
) else (
    echo [FEIL] En eller flere tester feilet.
)

set "TOTAL=?"
set "PASSED=?"
set "FAILED=?"
set "ERRORS=?"
set "SKIPPED=?"
if exist "docs\test-results\.last-test-summary.txt" (
    for /f "usebackq tokens=1,* delims==" %%A in ("docs\test-results\.last-test-summary.txt") do (
        if "%%A"=="TOTAL" set "TOTAL=%%B"
        if "%%A"=="PASSED" set "PASSED=%%B"
        if "%%A"=="FAILED" set "FAILED=%%B"
        if "%%A"=="ERRORS" set "ERRORS=%%B"
        if "%%A"=="SKIPPED" set "SKIPPED=%%B"
    )
)

echo.
echo ========================================
echo   Testoppsummering
echo ========================================
echo   Tester kjort:        %TOTAL%
echo   Bestatt:             %PASSED%
echo   Feilet:              %FAILED%
echo   Feil under kjoring:  %ERRORS%
echo   Hoppet over:         %SKIPPED%
echo ========================================
echo.
pause
exit /b %EXITCODE%
