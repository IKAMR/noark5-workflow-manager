@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Sjekker Python...
py --version >nul 2>&1

if %errorlevel% neq 0 (
    echo [FEIL] Python launcher ikke funnet.
    echo Installer Python fra:
    echo https://www.python.org/
    echo.
    echo Husk aa velge:
    echo - Install launcher for all users
    echo - Add Python to PATH
    pause
    exit /b 1
)

echo [OK] Python funnet via py launcher.
echo.

REM ------------------------------------------------------------
REM LibreOffice-sjekk var tidligere brukt i install_fix-1.bat.
REM Den er forelopig deaktivert for Noark 5 Workflow Manager,
REM siden dagens operasjoner ikke krever LibreOffice.
REM
REM Tidligere kontroll:
REM
REM echo Sjekker LibreOffice...
REM where soffice >nul 2>&1
REM if %errorlevel% neq 0 (
REM     if exist "C:\Program Files\LibreOffice\program\soffice.exe" (
REM         echo [OK] LibreOffice funnet.
REM     ) else (
REM         echo [FEIL] LibreOffice ikke funnet.
REM         echo Installer LibreOffice fra:
REM         echo https://www.libreoffice.org/
REM         pause
REM         exit /b 1
REM     )
REM ) else (
REM     echo [OK] LibreOffice funnet i PATH.
REM )
REM echo.
REM ------------------------------------------------------------

echo Installerer avhengigheter...
py -m pip install --disable-pip-version-check -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [FEIL] Installasjon av avhengigheter feilet.
    pause
    exit /b 1
)

echo.
echo [OK] Installasjon ferdig.
echo.
echo Starter Noark 5 Workflow Manager...
py main.py

pause