@echo off
title Rural Edu AI - Starting Project
cd /d "%~dp0"

echo ============================================
echo  Rural Digital Education - Starting...
echo ============================================
echo.
echo Step 1: Installing backend packages...
cd backend
python -m pip install -r requirements.txt -q 2>nul
cd ..

echo Step 2: Opening BACKEND window (keep it open!)...
start "Rural Edu - BACKEND (do not close)" cmd /k "cd /d "%~dp0backend" && echo Backend running at http://localhost:5000 && echo. && python run.py"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo Step 3: Installing frontend packages...
cd /d "%~dp0"
call npm install --prefix frontend

echo Step 4: Opening FRONTEND window...
start "Rural Edu - FRONTEND" cmd /k "cd /d "%~dp0" && echo Frontend: http://localhost:5173 && echo. && npm run dev"

echo.
echo ============================================
echo  DONE! Two windows opened:
echo  1) BACKEND  - must stay open (port 5000)
echo  2) FRONTEND - open http://localhost:5173
echo ============================================
echo.
pause
