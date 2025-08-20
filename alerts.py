
from datetime import date, timedelta
from models import Document, Company
from notifications import send_email, send_whatsapp

def build_message(docs, title):
    lines = [title, "" ]
    for d in docs:
        emp = d.company.razao_social if d.company else ""
        lines.append(f"- {emp} | {d.tipo.nome if d.tipo else ''} | {d.descricao or ''} | vence: {d.data_vencimento}")
    return "\n".join(lines)

def send_alerts():
    hoje = date.today()
    em_7 = hoje + timedelta(days=7)
    em_30 = hoje + timedelta(days=30)

    sets = [
        ("Documentos Vencidos", Document.query.filter(Document.data_vencimento < hoje).all()),
        ("Documentos a vencer (7 dias)", Document.query.filter(Document.data_vencimento >= hoje, Document.data_vencimento <= em_7).all()),
        ("Documentos a vencer (30 dias)", Document.query.filter(Document.data_vencimento > em_7, Document.data_vencimento <= em_30).all()),
    ]

    for title, docs in sets:
        if not docs: continue
        by_company = {}
        for d in docs:
            cid = d.company_id or 0
            by_company.setdefault(cid, []).append(d)
        for cid, items in by_company.items():
            comp = Company.query.get(cid) if cid else None
            message = build_message(items, title)
            emails = (comp.alert_email or "").split(";") if comp else []
            whats = (comp.alert_whatsapp or "").split(";") if comp else []
            if emails:
                send_email(emails, f"[Alertas] {title}", message)
            if whats:
                for w in whats:
                    send_whatsapp(w.strip(), message)
