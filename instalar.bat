@echo off
chcp 65001 >nul
title InOut Veículos — Instalação Inicial

echo.
echo  ============================================
echo   InOut Veículos — Instalação Inicial
echo  ============================================
echo.

:: Verifica se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado.
    echo  Baixe em: https://www.python.org/downloads/
    echo  Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

:: Verifica se o Git está instalado
git --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Git nao encontrado.
    echo  Baixe em: https://git-scm.com/download/win
    pause
    exit /b 1
)

:: Entra na pasta do projeto (onde este .bat está)
cd /d "%~dp0"

echo  [1/4] Criando ambiente virtual dentro do projeto...
python -m venv .venv
if errorlevel 1 ( echo  [ERRO] Falha ao criar ambiente virtual. & pause & exit /b 1 )

echo  [2/4] Instalando dependencias...
call .\.venv\Scripts\activate
if errorlevel 1 ( echo  [ERRO] Falha ao ativar ambiente virtual. & pause & exit /b 1 )

pip install -r requirements.txt --quiet
if errorlevel 1 ( echo  [ERRO] Falha ao instalar dependencias. & pause & exit /b 1 )

echo  [3/4] Inicializando banco de dados...
python seed.py
if errorlevel 1 ( echo  [ERRO] Falha ao inicializar banco. & pause & exit /b 1 )

echo.
echo  [4/4] Tudo pronto!
echo.
echo  ============================================
echo   Instalacao concluida com sucesso!
echo   Para iniciar o sistema, execute:
echo     iniciar.bat
echo  ============================================
echo.
pause
