@echo off
cls

echo ======================================
echo   AUTOMACAO DE OS - INICIALIZACAO
echo ======================================
echo.

REM ================================
REM 1. VERIFICAR PYTHON
REM ================================
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    echo Instale o Python 3.11 ou superior.
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b
)

REM ================================
REM 2. CRIAR VENV (SE NAO EXISTIR)
REM ================================
if not exist .venv (
    echo [INFO] Criando ambiente virtual...
    python -m venv .venv
)

REM ================================
REM 3. ATIVAR VENV
REM ================================
call .venv\Scripts\activate

REM ================================
REM 4. ATUALIZAR PIP
REM ================================
python -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
    echo Verifique o requirements.txt
    pause
    exit /b
)

REM ================================
REM 5. INSTALAR DEPENDENCIAS
REM ================================
if exist requirements.txt (
    echo [INFO] Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar dependencias.
    echo Verifique o requirements.txt
    pause
    exit /b
)
) else (
    echo [ERRO] requirements.txt nao encontrado.
    pause
    exit /b
)

REM ================================
REM 6. INSTALAR NAVEGADORES PLAYWRIGHT
REM ================================
echo [INFO] Verificando navegadores Playwright...
playwright install
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar navegadores Playwright.
    pause
    exit /b
)

REM ================================
REM 6. VERIFICAR .ENV
REM ================================
if not exist .env (
    echo [ERRO] Arquivo .env nao encontrado.
    echo Crie o .env com base no .env.example
    echo.
    pause
    exit /b
)

REM ================================
REM 7. EXECUTAR AUTOMACAO
REM ================================
echo.
echo [INFO] Executando automacao...
echo.

python automacao_os.py

REM ================================
REM 8. FINALIZACAO
REM ================================
echo.
echo ======================================
echo   PROCESSO FINALIZADO
echo ======================================
pause
