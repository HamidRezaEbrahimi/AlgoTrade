@echo off
chcp 65001 > nul
title Stop AlgoTrade Platform

echo ===============================================================================
echo            🛑 STOPPING ALGOTRADE PLATFORM SERVICES 🛑
echo ===============================================================================
echo.

echo [*] Stopping uvicorn and node (Vite) processes...
taskkill /f /im uvicorn.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq AlgoTrade Backend*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq AlgoTrade Frontend*" >nul 2>&1

echo [✓] AlgoTrade Backend and Frontend stopped.
echo.
echo Note: Docker containers (PostgreSQL & Redis) were kept running.
echo To stop Docker containers manually:
echo   docker stop Alef-DB Alef-Redis Alef-AdminDB Alef-RedisInsight
echo.
pause
