PDV (Caixa rápido) - Instruções rápidas

1) Dependência para USB (Windows):
   .venv\Scripts\activate
   pip install pywin32

2) Variáveis no .env (use a opção que você tiver):
   # Para USB (só o nome da impressora):
   TICKET_PRINTER_NAME=EPSON TM-T20 ReceiptE4

   # Se for impressora de REDE:
   # TICKET_PRINTER_HOST=192.168.0.50
   # TICKET_PRINTER_PORT=9100

   # Largura (40 para 80mm, 32 para 58mm):
   TICKET_COLS=40

3) Registrar o blueprint no app.py (adicione estas linhas após os outros blueprints):
   from blueprints.pdv.routes import pdv_bp
   app.register_blueprint(pdv_bp)

4) Criar tabela (se você usa migrations):
   set FLASK_APP=app.py
   flask db migrate -m "pdv cash movement"
   flask db upgrade

5) Rotas:
   /pdv             → formulário de lançamento (venda/sangria/retirada) + impressão
   /pdv/mov         → últimos lançamentos
   /pdv/test-print  → imprime teste

Obs: lançamentos de SANGRIA/RETIRADA imprimem área de assinatura no ticket.
