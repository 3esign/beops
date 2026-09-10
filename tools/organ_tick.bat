@echo off
rem BEOPS organ tick - scheduled task Beops_Organ, every 10 minutes.
rem One bounded pass of the news-sorter organ over the headlines the collector received.
rem A small local model on a CPU takes minutes, so the batch is deliberately small; the organ is
rem allowed to be silent and its silence is a receipt.
rem C-014: BEOPS_PYTHON may be a .cmd file. A batch that runs another batch WITHOUT `call`
rem hands over control and never comes back, so every line below it is silently skipped.
call "%~dp0beops_env.bat" || exit /b 9
cd /d "%BEOPS_ROOT%" || exit /b 9
if not exist runtime mkdir runtime
set BEOPS_ORGAN_LIMIT=10
set BEOPS_ORGAN_BATCH=5
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\organ-tick.log
call "%BEOPS_PYTHON%" -X utf8 -B tools\organ_news.py run >> runtime\organ-tick.log 2>&1
exit /b %ERRORLEVEL%
