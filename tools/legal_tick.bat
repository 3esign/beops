@echo off
rem BEOPS legal tick - scheduled task Beops_Legal, weekly: re-capture the permission evidence of every
rem source the collector polls. A permission captured once is a claim about one day; robots.txt and
rem Content-Signal change without notice. If a source is no longer permitted, the collector's own gate
rem (newest ledger line wins) stops it at the next tick - nothing else needs to change.
cd /d "D:\Svemir\!Projekti\Beops"
if not exist runtime mkdir runtime
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\legal-tick.log
C:\Svemir\python.cmd -X utf8 -B tools\legal_capture.py --recheck-collectors >> runtime\legal-tick.log 2>&1
