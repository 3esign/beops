@echo off
call "%~dp0beops_env.bat" || exit /b 9
cd /d "%BEOPS_ROOT%" || exit /b 9
if not exist runtime mkdir runtime
node tools\ai_feed.js tick >> runtime\ai-feed-tick.log 2>&1
exit /b %ERRORLEVEL%
