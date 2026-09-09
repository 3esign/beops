@echo off
set PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
cd /d D:\Svemir\!Projekti\Beops || exit /b 9
"%PY%" -X utf8 -B tools\guard.py >> data\live\guard.log 2>&1
exit /b 0
