@echo off
setlocal ENABLEDELAYEDEXPANSION

set PORT=5000
set HOST=0.0.0.0
set FLASK_APP=app.py

REM === Raiz do projeto = pasta deste .bat ===
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM === Checa admin ===
net session >nul 2>&1
if %errorLevel% NEQ 0 (
  echo [!] Este script precisa de permissao de ADMINISTRADOR.
  pause
  exit /b 1
)

echo [i] Projeto: %PROJECT_DIR%

REM === Libera firewall na porta (todos os perfis) ===
netsh advfirewall firewall add rule name="Flask %PORT%" dir=in action=allow protocol=TCP localport=%PORT% >nul 2>&1

REM === Escolhe Python do venv se existir ===
set "VENV_PY=%PROJECT_DIR%\.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
  set PYTHON=%VENV_PY%
) else (
  set PYTHON=python
)

set FLASK_APP=%FLASK_APP%
echo [i] Usando Python: %PYTHON%
echo [i] Iniciando Flask em http://0.0.0.0:%PORT%  (acesse via http://SEU_IP:%PORT% na LAN)

call "%PYTHON%" -V
call "%PYTHON%" -m flask --version

REM === Executa e mantem janela aberta para ver erros ===
call "%PYTHON%" -m flask run --host=%HOST% --port=%PORT%
set ERR=%ERRORLEVEL%

echo.
if %ERR% NEQ 0 (
  echo [x] Flask encerrou com erro (codigo %ERR%). Veja as mensagens acima.
) else (
  echo [i] Flask finalizado.
)
echo.
pause
endlocal
