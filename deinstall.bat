@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "APP_DIR=%LOCALAPPDATA%\Programs\Noark5WorkflowManager"
set "N5WF_BIN=%APP_DIR%\bin"
set "N5WF_LAUNCHER=%N5WF_BIN%\n5wf.cmd"
set "STATE_FILE=%APP_DIR%\install-state.json"
set "MODE=%~1"
set "CURRENT_GUI=0"
set "CURRENT_CLI=0"

call :read_state

if /I "%MODE%"=="all" goto mode_ok
if /I "%MODE%"=="gui" goto mode_ok
if /I "%MODE%"=="cli" goto mode_ok
if not "%MODE%"=="" goto usage

echo Noark 5 Workflow Manager - deinstallasjon
echo.
echo Registrert status:
echo   Core: %CURRENT_CORE%
echo   GUI:  %CURRENT_GUI%
echo   CLI:  %CURRENT_CLI%
echo.
echo   1. GUI + CLI
echo   2. GUI
echo   3. CLI
echo   4. Avbryt
echo.
set /p "CHOICE=Velg 1-4: "
if "%CHOICE%"=="1" set "MODE=all"
if "%CHOICE%"=="2" set "MODE=gui"
if "%CHOICE%"=="3" set "MODE=cli"
if "%CHOICE%"=="4" exit /b 0
if not defined MODE (
 echo [FEIL] Ugyldig valg.
 pause
 exit /b 2
)

:mode_ok
echo.
echo Valgt deinstallasjon: %MODE%
echo.
echo Dette slettes IKKE:
echo   repository/kildekode
echo   jobblister, logger, config eller andre brukerdata
echo   generelle Python-pakker som kan brukes av andre programmer
echo.
set /p "CONFIRM=Vil du fortsette? Skriv Ja eller Nei: "
if /I "%CONFIRM%"=="Nei" exit /b 0
if /I not "%CONFIRM%"=="Ja" (
 echo Avbrutt. Deinstallasjon krever eksplisitt Ja.
 pause
 exit /b 0
)

set "NEW_GUI=%CURRENT_GUI%"
set "NEW_CLI=%CURRENT_CLI%"

if /I "%MODE%"=="gui" set "NEW_GUI=0"
if /I "%MODE%"=="cli" set "NEW_CLI=0"
if /I "%MODE%"=="all" (
 set "NEW_GUI=0"
 set "NEW_CLI=0"
)

if /I "%MODE%"=="cli" call :remove_cli
if /I "%MODE%"=="all" call :remove_cli

set "NEW_CORE=0"
if "%NEW_GUI%"=="1" set "NEW_CORE=1"
if "%NEW_CLI%"=="1" set "NEW_CORE=1"

if "%NEW_CORE%"=="1" (
 call :write_state
) else (
 if exist "%STATE_FILE%" del /q "%STATE_FILE%"
 if exist "%N5WF_BIN%" rmdir "%N5WF_BIN%" 2>nul
 if exist "%APP_DIR%" rmdir "%APP_DIR%" 2>nul
)

echo.
echo [OK] Deinstallasjon fullfoert: %MODE%
echo Registrert status etterpaa:
echo   Core: %NEW_CORE%
echo   GUI:  %NEW_GUI%
echo   CLI:  %NEW_CLI%
if /I "%MODE%"=="cli" echo Lukk gamle terminaler for aa oppdatere PATH-miljoeet.
if /I "%MODE%"=="all" echo Lukk gamle terminaler for aa oppdatere PATH-miljoeet.
echo.
pause
exit /b 0

:remove_cli
echo.
echo Fjerner CLI-registrering...
if exist "%N5WF_LAUNCHER%" del /q "%N5WF_LAUNCHER%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$bin='%N5WF_BIN%'; $p=[Environment]::GetEnvironmentVariable('Path','User'); if($null -eq $p){exit 0}; $parts=@(); foreach($item in $p.Split(';')){if(-not [string]::IsNullOrWhiteSpace($item) -and -not [string]::Equals($item.Trim().TrimEnd('\'),$bin.TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)){$parts += $item.Trim()}}; [Environment]::SetEnvironmentVariable('Path',[string]::Join(';',$parts),'User')"
if errorlevel 1 echo [ADVARSEL] Klarte ikke aa rydde launcher-mappen fra bruker-PATH.

py -m pip uninstall -y noark5-workflow-manager >nul 2>&1
exit /b 0

:read_state
if exist "%STATE_FILE%" (
 for /f "tokens=1,2" %%A in ('powershell -NoProfile -Command "$s=ConvertFrom-Json -InputObject (Get-Content -Raw -LiteralPath '%STATE_FILE%'); $g=if($s.gui){1}else{0}; $c=if($s.cli){1}else{0}; Write-Output ($g.ToString()+' '+$c.ToString())"') do (
  set "CURRENT_GUI=%%A"
  set "CURRENT_CLI=%%B"
 )
) else (
 rem Migrering fra a7: eksisterende launcher betyr at CLI allerede er installert.
 if exist "%N5WF_LAUNCHER%" set "CURRENT_CLI=1"
)
set "CURRENT_CORE=0"
if "%CURRENT_GUI%"=="1" set "CURRENT_CORE=1"
if "%CURRENT_CLI%"=="1" set "CURRENT_CORE=1"
exit /b 0

:write_state
if not exist "%APP_DIR%" mkdir "%APP_DIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$state=[ordered]@{version='0.1.2-a8'; core=$true; gui=('%NEW_GUI%' -eq '1'); cli=('%NEW_CLI%' -eq '1')}; $json=ConvertTo-Json -InputObject $state; Set-Content -Encoding UTF8 -LiteralPath '%STATE_FILE%' -Value $json"
exit /b %errorlevel%

:usage
echo Bruk: deinstall.bat [all^|gui^|cli]
exit /b 2
