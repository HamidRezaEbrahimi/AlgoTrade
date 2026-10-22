# start.ps1 - PowerShell Launcher for AlgoTrade Platform
$Host.UI.RawUI.WindowTitle = "AlgoTrade Platform Launcher"

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "            ALGOTRADE MULTI-MARKET PLATFORM LAUNCHER                          " -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check and Start Docker Containers (PostgreSQL & Redis)
Write-Host "[*] Checking Docker containers: Alef-DB and Alef-Redis..." -ForegroundColor White

try {
    $runningContainers = docker ps --format "{{.Names}}" 2>$null
    
    if ($runningContainers -notmatch "Alef-DB") {
        Write-Host "[!] Alef-DB is not running. Starting from D:\Docker\ImageData\PostgreSQL..." -ForegroundColor Yellow
        if (Test-Path "D:\Docker\ImageData\PostgreSQL\docker-compose.yml") {
            Push-Location "D:\Docker\ImageData\PostgreSQL"
            docker compose up -d
            Pop-Location
        } else {
            Write-Warning "PostgreSQL compose file not found at D:\Docker\ImageData\PostgreSQL\docker-compose.yml"
        }
    } else {
        Write-Host "[OK] Alef-DB (PostgreSQL 18) is running on port 5432." -ForegroundColor Green
    }

    if ($runningContainers -notmatch "Alef-Redis") {
        Write-Host "[!] Alef-Redis is not running. Starting from D:\Docker\ImageData\Redis..." -ForegroundColor Yellow
        if (Test-Path "D:\Docker\ImageData\Redis\docker-compose.yml") {
            Push-Location "D:\Docker\ImageData\Redis"
            docker compose up -d
            Pop-Location
        } else {
            Write-Warning "Redis compose file not found at D:\Docker\ImageData\Redis\docker-compose.yml"
        }
    } else {
        Write-Host "[OK] Alef-Redis is running on port 6379." -ForegroundColor Green
    }
} catch {
    Write-Warning "Docker daemon might not be running. Continuing..."
}

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "[*] Launching AlgoTrade Backend with Hot-Reload for AlefTrade and App..." -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan

# Start Backend in separate window
Start-Process -FilePath "cmd.exe" -ArgumentList '/k', 'title AlgoTrade Backend (FastAPI + AlefTrade) && cd /d G:\Projects\AlgoTrade\backend && echo Starting FastAPI Backend on http://127.0.0.1:8000 ... && uv run uvicorn main:app --reload --reload-dir app --reload-dir G:\Projects\AlefTrade --host 127.0.0.1 --port 8000'

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "[*] Launching AlgoTrade Frontend (Vite + React)..." -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan

# Start Frontend in separate window
Start-Process -FilePath "cmd.exe" -ArgumentList '/k', 'title AlgoTrade Frontend (Vite Dev Server) && cd /d G:\Projects\AlgoTrade\frontend && echo Starting Vite Frontend on http://localhost:5173 ... && npm run dev'

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "[OK] All services successfully launched!" -ForegroundColor Green
Write-Host ""
Write-Host "  - Frontend Terminal : http://localhost:5173/" -ForegroundColor Cyan
Write-Host "  - Backend Swagger   : http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  - pgAdmin           : http://localhost:5050 (admin@local.com / admin123)" -ForegroundColor Yellow
Write-Host "  - RedisInsight      : http://localhost:5540" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Note: Any edits in G:\Projects\AlefTrade or backend\app\" -ForegroundColor Magenta
Write-Host "        will trigger instant hot-reload without restart!" -ForegroundColor Magenta
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host ""
