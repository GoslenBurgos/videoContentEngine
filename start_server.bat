@echo off
title Skytech Content Engine Server (Local RTX 5060 Ti GPU Engine)
color 0A
echo ============================================================
echo 🚀 SKYTECH CONTENT ENGINE | Servidor Web Local (GPU RTX 5060 Ti)
echo ============================================================
echo.
echo Iniciando servidor FastAPI en http://localhost:8500 ...
echo.
cd /d "%~dp0"
timeout /t 2 /nobreak >nul
start http://localhost:8500
python server.py
pause
