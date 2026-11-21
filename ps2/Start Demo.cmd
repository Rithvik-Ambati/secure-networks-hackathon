@echo off
title Flatland live demo launcher
echo ================================================
echo  Flatland live demo: starting everything
echo ================================================
echo.
echo [1/3] Docker Desktop...
docker info >nul 2>&1
if errorlevel 1 (
  start "" "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe"
  echo       waiting for Docker to be ready, this can take a minute...
)
:waitdocker
docker info >nul 2>&1
if errorlevel 1 (
  timeout /t 5 /nobreak >nul
  goto waitdocker
)
echo       Docker is ready.
echo.
echo [2/3] Dashboard server (a second window opens, leave it open)...
wsl -d Ubuntu -- pkill -f tools/dashboard.py >nul 2>&1
start "Flatland dashboard (leave open)" wsl -d Ubuntu -- bash /mnt/d/hackathon_prep/ps2/dashboard.sh
:waitdash
curl -s -o nul http://127.0.0.1:8765/
if errorlevel 1 (
  timeout /t 2 /nobreak >nul
  goto waitdash
)
echo       Dashboard is up.
echo.
echo [3/3] Opening http://127.0.0.1:8765 in your browser...
start "" http://127.0.0.1:8765
echo.
echo Click the buttons in order: 1, 2, 3, 4, then 5, 2, 3, 4, then 6 and 7.
echo Keep this window and the dashboard window open during the demo.
echo.
pause
