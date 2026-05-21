@echo off
cd /d "%~dp0frontend"
if not exist node_modules (
  echo Installing frontend dependencies...
  call npm install
)
echo.
echo Starting frontend on http://localhost:5173
call npm run dev
pause
