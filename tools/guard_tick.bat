@echo off
rem BEOPS guard tick - scheduled task Beops_Guard, every 15 minutes.
call "%~dp0beops_env.bat" || exit /b 9
cd /d "%BEOPS_ROOT%" || exit /b 9
if not exist runtime mkdir runtime
if not exist data\live mkdir data\live
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\guard-tick.log
call "%BEOPS_PYTHON%" -X utf8 -B tools\guard.py >> data\live\guard.log 2>&1
set RC=%ERRORLEVEL%
echo guard exit %RC% >> runtime\guard-tick.log
exit /b %RC%
