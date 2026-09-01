@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "N5WF_BIN=%LOCALAPPDATA%\Programs\Noark5WorkflowManager\bin"
set "N5WF_LAUNCHER=%N5WF_BIN%\n5wf.cmd"

echo Sjekker Python...
py --version >nul 2>&1
if errorlevel 1 (
 echo [FEIL] Python launcher "py" ble ikke funnet.
 pause
 exit /b 1
)
echo [OK] Python funnet via py launcher.

echo.
echo Installerer avhengigheter...
py -m pip install --disable-pip-version-check --user -r requirements.txt
if errorlevel 1 (
 echo [FEIL] Installasjon av avhengigheter feilet.
 pause
 exit /b 1
)

echo.
echo Installerer Noark 5 Workflow Manager...
py -m pip install --disable-pip-version-check --user --no-deps -e .
if errorlevel 1 (
 echo [FEIL] Installasjon av Noark 5 Workflow Manager feilet.
 pause
 exit /b 1
)

echo.
echo Oppretter stabil n5wf-launcher...
if not exist "%N5WF_BIN%" mkdir "%N5WF_BIN%"
> "%N5WF_LAUNCHER%" echo @echo off
>> "%N5WF_LAUNCHER%" echo py -m noark5_workflow.cli %%*
>> "%N5WF_LAUNCHER%" echo exit /b %%errorlevel%%

if not exist "%N5WF_LAUNCHER%" (
 echo [FEIL] Klarte ikke aa opprette n5wf.cmd.
 pause
 exit /b 1
)

echo [OK] Launcher opprettet:
echo %N5WF_LAUNCHER%

echo.
echo Tester launcheren direkte...
call "%N5WF_LAUNCHER%" --version
if errorlevel 1 (
 echo [FEIL] Launcheren kunne ikke starte CLI.
 pause
 exit /b 1
)
echo [OK] Launcher virker.

echo.
echo Registrerer launcher-mappen i bruker-PATH...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$bin='%N5WF_BIN%'; $p=[Environment]::GetEnvironmentVariable('Path','User'); if($null -eq $p){$p=''}; $parts=@($p -split ';' | ForEach-Object {$_.Trim()} | Where-Object {$_}); $found=@($parts | Where-Object {[string]::Equals($_.TrimEnd('\'),$bin.TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)}).Count -gt 0; if(-not $found){$new=if($p.Trim()){$p.TrimEnd(';')+';'+$bin}else{$bin}; [Environment]::SetEnvironmentVariable('Path',$new,'User'); Write-Host '[OK] Launcher-mappen er lagt til i bruker-PATH.'}else{Write-Host '[OK] Launcher-mappen finnes allerede i bruker-PATH.'}"
if errorlevel 1 (
 echo [FEIL] Klarte ikke aa oppdatere bruker-PATH.
 pause
 exit /b 1
)

echo.
echo [OK] n5wf er installert og launcheren er testet.
echo Launcher:
echo   %N5WF_LAUNCHER%
echo.
echo Lukk alle gamle PowerShell/CMD/Windows Terminal-prosesser.
echo Aapne en helt ny terminal og test:
echo   n5wf --version
echo   n5wf --help
echo.
echo GUI startes fortsatt med start.bat
pause
exit /b 0
