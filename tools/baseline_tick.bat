@echo off
rem BEOPS baseline tick - scheduled task Beops_Baseline, hourly.
rem A full publish already rebuilds the same views from a frozen capture. Do not
rem make both disk-heavy readers compete on the 8 GB observatory body.
if exist "%~dp0..\runtime\publish-preparation.lock" exit /b 0
if exist "%~dp0..\runtime\publish.lock" exit /b 0
call "%~dp0beops_env.bat"
if errorlevel 1 exit /b %ERRORLEVEL%
cd /d "%BEOPS_ROOT%" || exit /b 9
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0baseline_run.ps1" -ProjectRoot "%BEOPS_ROOT%" -PythonPath "%BEOPS_PYTHON%" -TimeoutSeconds 1200
exit /b %ERRORLEVEL%
