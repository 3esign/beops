@echo off
rem BEOPS legal tick - scheduled task Beops_Legal, weekly: re-capture the permission evidence of every
rem source the collector polls. A permission captured once is a claim about one day; robots.txt and
rem Content-Signal change without notice. If a source is no longer permitted, the collector's own gate
rem (newest ledger line wins) stops it at the next tick - nothing else needs to change.
rem C-014: C:\Svemir\python.cmd is a .cmd file. A batch that runs another batch WITHOUT `call`
rem hands over control and never comes back, so every line below it is silently skipped.
cd /d "D:\Svemir\!Projekti\Beops"
if not exist runtime mkdir runtime
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\legal-tick.log
call C:\Svemir\python.cmd -X utf8 -B tools\legal_capture.py --recheck-collectors >> runtime\legal-tick.log 2>&1
