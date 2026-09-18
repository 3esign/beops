@echo off
rem Shared environment for BEOPS scheduled ticks. The batch lives in tools/,
rem so its parent is the project root no matter whether the tree is entered
rem through C:\Svemir or D:\Svemir.
set "BEOPS_ROOT=%~dp0.."
if exist "%BEOPS_ROOT%\runtime\MAINTENANCE" (
  echo BEOPS is paused for maintenance. No job was started.
  exit /b 75
)
rem Keep temporary collector/build files with the physical project.
set "TEMP=%BEOPS_ROOT%\runtime\tmp"
set "TMP=%TEMP%"
if not exist "%TEMP%" mkdir "%TEMP%"
if not defined BEOPS_MODEL_BACKEND set "BEOPS_MODEL_BACKEND=cli"
if not defined BEOPS_PYTHON (
  if exist "%USERPROFILE%\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe" (
    set "BEOPS_PYTHON=%USERPROFILE%\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
  ) else if exist "C:\Svemir\python.cmd" (
    set "BEOPS_PYTHON=C:\Svemir\python.cmd"
  ) else (
    set "BEOPS_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  )
)
if not defined BEOPS_TEST_PYTHON if not exist "%BEOPS_ROOT%\runtime\test-python.json" (
  if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "BEOPS_TEST_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  ) else (
    set "BEOPS_TEST_PYTHON=%BEOPS_PYTHON%"
  )
)
if not exist "%BEOPS_PYTHON%" (
  echo BEOPS_PYTHON does not exist: %BEOPS_PYTHON%
  exit /b 9
)
if defined BEOPS_TEST_PYTHON if not exist "%BEOPS_TEST_PYTHON%" (
  echo BEOPS_TEST_PYTHON does not exist: %BEOPS_TEST_PYTHON%
  exit /b 9
)
if not exist "%BEOPS_ROOT%" (
  echo BEOPS_ROOT does not exist: %BEOPS_ROOT%
  exit /b 9
)
exit /b 0
