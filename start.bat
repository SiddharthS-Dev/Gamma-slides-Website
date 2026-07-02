@echo off
title SlideVault
color 0B
echo ===================================================
echo              SLIDEVAULT LAUNCHER
echo ===================================================
echo.

:: ── Locate Python ────────────────────────────────────────────────────────────
set PYTHON=
if exist "%~dp0backend\venv\Scripts\python.exe" (
    set PYTHON=%~dp0backend\venv\Scripts\python.exe
    goto check_dist
)
py --version >nul 2>&1
if %ERRORLEVEL% equ 0 ( set PYTHON=py & goto check_dist )
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 ( set PYTHON=python & goto check_dist )

color 0C
echo [ERROR] Python not found. Install Python 3.11+ or re-create the venv.
pause & exit /b 1

:: ── Build frontend if dist is missing or stale ───────────────────────────────
:check_dist
if not exist "%~dp0frontend\dist\index.html" (
    echo [1/2] Building frontend ^(first run or dist missing^)...
    npm --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [ERROR] npm not found. Install Node.js to build the frontend.
        pause & exit /b 1
    )
    pushd "%~dp0frontend"
    call npm run build
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [ERROR] Frontend build failed.
        popd & pause & exit /b 1
    )
    popd
    echo [1/2] Frontend built successfully.
) else (
    echo [1/2] Frontend dist found — skipping build.
)

:: ── Launch single-port server ────────────────────────────────────────────────
echo [2/2] Starting SlideVault on http://localhost:8000 ...
echo.
echo ===================================================
echo   App:      http://localhost:8000
echo   API Docs: http://localhost:8000/api/docs
echo   Press Ctrl+C to stop.
echo ===================================================
echo.

cd /d "%~dp0backend"
"%PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
