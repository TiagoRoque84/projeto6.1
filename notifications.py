# notifications.py

import os, smtplib
from email.message import EmailMessage
import requests

# --- FUNÇÃO DE E-MAIL ATUALIZADA PARA ACEITAR ANEXOS ---
def send_email(to_list, subject, body, attachment_path=None, attachment_filename=None):
    # Atualizado para usar MAIL_SERVER ao invés de SMTP_HOST
    host = os.getenv("MAIL_SERVER")
    if not host:
        print("⚠️  AVISO: E-mail não configurado (MAIL_SERVER vazio no .env)")
        print("📧 Configuração necessária:")
        print("   MAIL_SERVER=smtp.gmail.com")
        print("   MAIL_PORT=587")
        print("   MAIL_USERNAME=seu_email@gmail.com")
        print("   MAIL_PASSWORD=sua_senha_app")
        return False, "E-mail não configurado"
    
    port = int(os.getenv("MAIL_PORT","587"))
    user = os.getenv("MAIL_USERNAME")
    pwd  = os.getenv("MAIL_PASSWORD")
    from_addr = os.getenv("MAIL_DEFAULT_SENDER", user)
    
    if not user or not pwd:
        print("⚠️  AVISO: Credenciais de e-mail não configuradas")
        return False, "Credenciais não configuradas"
    
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join([t.strip() for t in to_list if t.strip()])
    msg.set_content(body)

    # Lógica para adicionar o anexo, se houver
    if attachment_path and attachment_filename:
        try:
            with open(attachment_path, 'rb') as f:
                file_data = f.read()
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=attachment_filename)
        except FileNotFoundError:
            print(f"ERRO: Arquivo de anexo não encontrado em {attachment_path}")
            return False, "Arquivo de anexo não encontrado"

    try:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            if user: s.login(user, pwd)
            s.send_message(msg)
        print(f"✅ E-mail enviado com sucesso para: {', '.join(to_list)}")
        return True, "E-mail enviado com sucesso."
    except Exception as e:
        print(f"❌ ERRO ao enviar e-mail: {e}")
        return False, f"Falha no envio: {e}"

# --- FUNÇÃO DE WHATSAPP (SEM ALTERAÇÃO) ---
def send_whatsapp(to_number, body):
    if os.getenv("WHATSAPP_PROVIDER") != "twilio": return
    sid = os.getenv("TWILIO_SID"); token = os.getenv("TWILIO_TOKEN"); from_ = os.getenv("TWILIO_FROM")
    if not sid or not token or not from_: return
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = {"To": f"whatsapp:{to_number}", "From": from_, "Body": body}
    requests.post(url, data=data, auth=(sid, token))