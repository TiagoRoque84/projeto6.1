
import os, smtplib
from email.message import EmailMessage
import requests

def send_email(to_list, subject, body):
    host = os.getenv("SMTP_HOST")
    if not host: return
    port = int(os.getenv("SMTP_PORT","587"))
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    from_addr = os.getenv("SMTP_FROM", user)
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join([t.strip() for t in to_list if t.strip()])
    msg.set_content(body)
    with smtplib.SMTP(host, port) as s:
        s.starttls()
        if user: s.login(user, pwd)
        s.send_message(msg)

def send_whatsapp(to_number, body):
    if os.getenv("WHATSAPP_PROVIDER") != "twilio": return
    sid = os.getenv("TWILIO_SID"); token = os.getenv("TWILIO_TOKEN"); from_ = os.getenv("TWILIO_FROM")
    if not sid or not token or not from_: return
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = {"To": f"whatsapp:{to_number}", "From": from_, "Body": body}
    requests.post(url, data=data, auth=(sid, token))
