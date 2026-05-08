@echo off
setlocal

cd /d "%~dp0"

echo [1/4] Checking required commands...
where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] docker not found. Please install/start Docker Desktop first.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found. Please install Node.js.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python not found. Please install Python 3.
  pause
  exit /b 1
)

echo [2/4] Starting Docker services...
docker compose up -d
if errorlevel 1 (
  echo [ERROR] docker compose failed. Check Docker Desktop status.
  pause
  exit /b 1
)

echo [3/4] Starting backend on port 8000...
start "Backend - FastAPI" cmd /k "cd /d ""%~dp0"" && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [4/4] Starting frontend on port 5174...
start "Frontend - Vite" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo Opening frontend in browser...
timeout /t 2 /nobreak >nul
start "" "http://localhost:5174"

echo.
echo Project startup commands have been launched.
echo Frontend: http://localhost:5174
echo Backend : http://localhost:8000/api/all
echo.
echo You can close this window now.
pause

endlocal
