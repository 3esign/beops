@echo off
rem Objava BEZ kapije kadence. Kapija memorije i baterija OSTAJU.
rem Napisano 2026-09-24: sajt stoji 11 h, kazna bi istekla tek u 03:45, prezentacija je danas.
call "%~dp0beops_env.bat"
if errorlevel 1 exit /b %ERRORLEVEL%
cd /d "%BEOPS_ROOT%" || exit /b 9
if exist "runtime\PUBLISH_PAUSED" exit /b 0
if exist "runtime\MAINTENANCE" exit /b 75
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_capacity.ps1
if "%ERRORLEVEL%"=="75" exit /b 0
if not "%ERRORLEVEL%"=="0" exit /b 9
if not exist runtime mkdir runtime
echo ---- rucni tik bez kadence >> runtime\publish-tick-5.log
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_github.ps1 >> runtime\publish-tick-5.log 2>&1
exit /b %ERRORLEVEL%
