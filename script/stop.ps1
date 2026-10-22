# stop.ps1 - Stop AlgoTrade Platform services
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===============================================================================" -ForegroundColor Red
Write-Host "            🛑 STOPPING ALGOTRADE PLATFORM SERVICES 🛑                        " -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Red
Write-Host ""

Write-Host "[*] Terminating uvicorn and Vite processes..." -ForegroundColor White

Stop-Process -Name "uvicorn" -Force -ErrorAction SilentlyContinue
Get-Process | Where-Object { $_.MainWindowTitle -like "AlgoTrade Backend*" -or $_.MainWindowTitle -like "AlgoTrade Frontend*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "[✓] AlgoTrade Backend and Frontend stopped." -ForegroundColor Green
Write-Host ""
Write-Host "Note: Docker containers (PostgreSQL & Redis) were kept running." -ForegroundColor Gray
Write-Host "To stop Docker containers manually: docker stop Alef-DB Alef-Redis Alef-AdminDB Alef-RedisInsight" -ForegroundColor Gray
Write-Host ""
