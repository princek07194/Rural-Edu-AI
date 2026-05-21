@echo off
cd /d "%~dp0backend"
echo Installing backend dependencies (first time only)...
python -m pip install -r requirements.txt -q
echo.
echo Starting backend on http://localhost:5000
python run.py
pause
