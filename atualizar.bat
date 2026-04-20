@echo off
chcp 65001 >nul
title InOut Veículos — Atualização

echo.
echo  ============================================
echo   InOut Veículos — Aplicando Atualizações
echo  ============================================
echo.

cd /d "%~dp0"
call .\.venv\Scripts\activate
if errorlevel 1 (
    echo  [ERRO] Ambiente virtual nao encontrado.
    echo  Execute instalar.bat primeiro.
    pause
    exit /b 1
)

echo  [1/4] Baixando atualizacoes do GitHub...
git pull origin main
if errorlevel 1 (
    echo.
    echo  [AVISO] Nao foi possivel baixar atualizacoes.
    echo  Verifique sua conexao com a internet.
    pause
    exit /b 1
)

echo.
echo  [2/4] Atualizando dependencias...
pip install -r requirements.txt --quiet

echo.
echo  [3/4] Atualizando banco de dados...
python seed.py

echo.
echo  [4/4] Iniciando servidor...
echo.
echo  Servidor rodando em: http://127.0.0.1:5000
echo  Para encerrar pressione Ctrl+C
echo.
python run.py
pause
