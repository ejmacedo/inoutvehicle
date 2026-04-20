@echo off
chcp 65001 >nul
title InOut Veículos — Servidor

echo.
echo  ============================================
echo   InOut Veículos — Iniciando servidor...
echo  ============================================
echo.

cd /d "%~dp0"
call .\.venv\Scripts\activate
cd inoutvehicle

echo  Servidor rodando em: http://127.0.0.1:5000
echo  Para encerrar pressione Ctrl+C
echo.
python run.py
pause
