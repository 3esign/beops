@echo off
rem BEOPS mind tick - scheduled task Beops_Mind, every 4 minutes: ONE drop of the endless conversation.
rem Steps cycle: linker, observer, ranker, skeptic, connector, score. One or two local model calls per
rem step (a thought and its Serbian voice). The organ is allowed to be silent and its silence is a
rem receipt; a person stops it with data\live\derived\mind\PAUSED.
cd /d "D:\Svemir\!Projekti\Beops"
if not exist runtime mkdir runtime
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\mind-tick.log
C:\Svemir\python.cmd -X utf8 -B tools\organ_mind.py step >> runtime\mind-tick.log 2>&1
