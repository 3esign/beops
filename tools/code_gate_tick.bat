@echo off
rem BEOPS code gate tick - scheduled task Beops_CodeGate, every 30 minutes. The complete research
rem suite runs once per source commit (tools/code_gate.ps1); most ticks find a fresh receipt and exit.
cd /d "%~dp0.." || exit /b 9
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0code_gate.ps1"
exit /b %ERRORLEVEL%
