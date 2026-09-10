@echo off
rem BEOPS baseline tick - scheduled task Beops_Baseline, hourly.
call "%~dp0beops_env.bat" || exit /b 9
cd /d "%BEOPS_ROOT%" || exit /b 9
if not exist runtime mkdir runtime
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\baseline-tick.log
call "%BEOPS_PYTHON%" -X utf8 -B tools\baseline.py build >> runtime\baseline-tick.log 2>&1
exit /b %ERRORLEVEL%
