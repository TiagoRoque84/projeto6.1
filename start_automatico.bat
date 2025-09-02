@echo off
REM --- MUDE A LINHA ABAIXO PARA A PASTA DO SEU PROJETO ---
cd /d "C:\Users\Master\Desktop\projeto6-main"

REM --- INICIA O SERVIDOR E SOBRESCREVE O ARQUIVO DE LOG ---
echo Iniciando servidor em %DATE% %TIME% > server_log.txt
call .\.venv\Scripts\python.exe -m flask run --host=0.0.0.0 --port=5000 >> server_log.txt 2>&1