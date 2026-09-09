@echo off
rem Beops OBS-001 tick — jedan pokusaj snimka po terminu. Pravi ga claude-cowork 05.09.2026
rem zato sto automatizacija iz Codex sesije nije imala trajnog domacina (0/13 snimljeno).
rem Gasi sam sebe posle poslednjeg dozvoljenog termina (22:50 UTC + 5 min rezerve).
cd /d "D:\Svemir\!Projekti\Beops"
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyyMMddHHmm')"`) do set NOWUTC=%%i
echo ---- %DATE% %TIME% (utc %NOWUTC%) >> runtime\obs001-tick.log
C:\Svemir\python.cmd -B research\observe_10k.py capture >> runtime\obs001-tick.log 2>&1
if %NOWUTC% GTR 202609052255 schtasks /delete /tn Beops_OBS001 /f >> runtime\obs001-tick.log 2>&1
