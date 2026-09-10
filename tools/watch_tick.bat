@echo off
rem BEOPS watchman tick - scheduled task Beops_Watch, every 10 minutes.
rem It runs as its OWN task on purpose. A watchman hung off the pipeline it watches dies with it,
rem which is precisely the failure it exists to catch (C-014).
rem C-014: BEOPS_PYTHON may be a .cmd file. A batch that runs another batch WITHOUT `call`
rem hands over control and never comes back, so every line below it is silently skipped.
call "%~dp0beops_env.bat" || exit /b 9
cd /d "%BEOPS_ROOT%" || exit /b 9
if not exist runtime mkdir runtime
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\watch-tick.log
call "%BEOPS_PYTHON%" -X utf8 -B tools\watchman.py >> runtime\watch-tick.log 2>&1
exit /b %ERRORLEVEL%
