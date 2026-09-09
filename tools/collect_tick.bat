@echo off
rem Beops live collector tick - called by the scheduled task Beops_Collect every 5 minutes.
rem Made 2026-09-08 by claude-cowork. Transport is curl.exe (Schannel); Python is only the parser.
rem This file does NOT end itself: the schedule is owned by the scheduler and checked with
rem   schtasks /query /tn Beops_Collect     (C-011: a self-delete is not a deletion)
cd /d "D:\Svemir\!Projekti\Beops"
if not exist runtime mkdir runtime
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')"`) do set NOWUTC=%%i
echo ---- %NOWUTC% >> runtime\collect-tick.log
C:\Svemir\python.cmd -X utf8 -B tools\collect_daemon.py tick >> runtime\collect-tick.log 2>&1
