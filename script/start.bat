@echo off
title AlgoTrade Platform Launcher

echo ===============================================================================
echo            ALGOTRADE MULTI-MARKET PLATFORM LAUNCHER
echo ===============================================================================
echo.

REM 1. Check and Start Docker Containers
echo [*] Checking Docker containers: Alef-DB and Alef-Redis...

docker ps --format "{{.Names}}" | findstr /i "Alef-DB" > nul
if errorlevel 1 (
    echo [!] Alef-DB container is not running. Starting from D:\Docker\ImageData\PostgreSQL...
    if exist "D:\Docker\ImageData\PostgreSQL\docker-compose.yml" (
        pushd "D:\Docker\ImageData\PostgreSQL"
        docker compose up -d
        popd
    ) else (
        echo [!] Warning: PostgreSQL docker-compose.yml not found at D:\Docker\ImageData\PostgreSQL
    )
) else (
    echo [OK] Alef-DB - PostgreSQL 18 is running on port 5432.
)

docker ps --format "{{.Names}}" | findstr /i "Alef-Redis" > nul
if errorlevel 1 (
    echo [!] Alef-Redis container is not running. Starting from D:\Docker\ImageData\Redis...
    if exist "D:\Docker\ImageData\Redis\docker-compose.yml" (
        pushd "D:\Docker\ImageData\Redis"
        docker compose up -d
        popd
    ) else (
        echo [!] Warning: Redis docker-compose.yml not found at D:\Docker\ImageData\Redis
    )
) else (
    echo [OK] Alef-Redis is running on port 6379.
)

echo.
echo ===============================================================================
echo [*] Launching AlgoTrade Backend with Hot-Reload for AlefTrade and App...
echo ===============================================================================

start "AlgoTrade Backend" cmd /k "cd /d G:\Projects\AlgoTrade\backend && echo Starting FastAPI Backend on http://127.0.0.1:8000 ... && uv run uvicorn main:app --reload --reload-dir app --reload-dir G:\Projects\AlefTrade --host 127.0.0.1 --port 8000"

ping 127.0.0.1 -n 3 > nul

echo.
echo ===============================================================================
echo [*] Launching AlgoTrade Frontend (Vite + React)...
echo ===============================================================================

start "AlgoTrade Frontend" cmd /k "cd /d G:\Projects\AlgoTrade\frontend && echo Starting Vite Frontend on http://localhost:5173 ... && npm run dev"

echo.
echo ===============================================================================
echo [OK] All services successfully launched!
echo.
echo   - Frontend Terminal : http://localhost:5173/
echo   - Backend Swagger   : http://127.0.0.1:8000/docs
echo   - pgAdmin           : http://localhost:5050 - admin@local.com / admin123
echo   - RedisInsight      : http://localhost:5540
echo.
echo   Note: Any changes made inside G:\Projects\AlefTrade or backend\app\
echo         will automatically trigger a live backend reload!
echo ===============================================================================
echo.
