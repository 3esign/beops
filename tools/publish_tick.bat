@echo off
rem BEOPS publish tick - scheduled task Beops_Publish, every 10 minutes.
rem Exports the current tree (without the captured evidence) and the generated docs/ to
rem github.com/3esign/beops, so the public site shows the last receptions rather than a frozen day.
rem The schedule is owned by the scheduler and verified with: schtasks /query /tn Beops_Publish
rem C-014: C:\Svemir\python.cmd is a .cmd file. A batch that runs another batch WITHOUT `call`
rem hands over control and never comes back, so every line below it is silently skipped.
cd /d "D:\Svemir\!Projekti\Beops"
if not exist runtime mkdir runtime
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\publish-tick.log
call C:\Svemir\python.cmd -X utf8 -B tools\collect_daemon.py export >> runtime\publish-tick.log 2>&1
call C:\Svemir\python.cmd -X utf8 -B tools\collect_daemon.py report >> runtime\publish-tick.log 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_github.ps1 >> runtime\publish-tick.log 2>&1
