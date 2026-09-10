@echo off
rem Shared environment for BEOPS scheduled ticks. The batch lives in tools/,
rem so its parent is the project root no matter whether the tree is entered
rem through C:\Svemir or D:\Svemir.
set "BEOPS_ROOT=%~dp0.."
if not defined BEOPS_PYTHON (
  if exist "C:\Svemir\python.cmd" (
    set "BEOPS_PYTHON=C:\Svemir\python.cmd"
  ) else (
    set "BEOPS_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  )
)
if not defined BEOPS_TEST_PYTHON (
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
if not exist "%BEOPS_TEST_PYTHON%" (
  echo BEOPS_TEST_PYTHON does not exist: %BEOPS_TEST_PYTHON%
  exit /b 9
)
if not exist "%BEOPS_ROOT%" (
  echo BEOPS_ROOT does not exist: %BEOPS_ROOT%
  exit /b 9
)
exit /b 0
