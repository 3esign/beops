@echo off
rem BEOPS mind tick - scheduled task Beops_Mind, every 4 minutes: ONE drop of the endless conversation.
rem Steps cycle: linker, observer, ranker, skeptic, connector, score. A reviewed CLI or local fallback
rem produces one constrained bilingual response. Transient route failure keeps the same step for the
rem next tick; a person stops the organ with data\live\derived\mind\PAUSED.
rem C-014: BEOPS_PYTHON may be a .cmd file. A batch that runs another batch WITHOUT `call`
rem hands over control and never comes back, so every line below it is silently skipped.
call "%~dp0beops_env.bat"
if errorlevel 1 exit /b %ERRORLEVEL%
cd /d "%BEOPS_ROOT%" || exit /b 9
if not exist runtime mkdir runtime
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\mind-tick-live-2.log
call "%BEOPS_PYTHON%" -X utf8 -B tools\organ_mind.py step >> runtime\mind-tick-live-2.log 2>&1
exit /b %ERRORLEVEL%
