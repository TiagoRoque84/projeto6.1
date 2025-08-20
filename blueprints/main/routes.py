# blueprints/main/routes.py
from flask import Blueprint, jsonify
from flask_login import login_required
from datetime import date, datetime, timedelta
import os

from models import Employee
try:
    from models import Funcao
except Exception:
    Funcao = None
try:
    from models import Document, DocumentType
except Exception:
    Document = None
    DocumentType = None

main_bp = Blueprint("main", __name__, template_folder='../../templates')

@main_bp.route("/", endpoint="index")
@login_required
def index():
    # Usa a mesma view do painel (sem redirecionar e sem duplicar lógica)
    from blueprints.dash.routes import dashboard as dash_dashboard
    return dash_dashboard()

def _get_cnh_expiration(emp):
    # 1) tenta atributos comuns no modelo Employee
    for attr in ("cnh_vencimento", "cnh_validade", "cnh_expira_em", "validade_cnh"):
        if hasattr(emp, attr):
            val = getattr(emp, attr)
            if val:
                return val

    # 2) tenta via documentos relacionados (tipo 'CNH')
    try:
        docs = getattr(emp, "documents", None) or getattr(emp, "documentos", None)
        if docs:
            for d in docs:
                # Identifica se o doc é CNH
                name_ok = False
                try:
                    t = getattr(d, "tipo", None)
                    if t is not None:
                        nome_tipo = getattr(t, "nome", None)
                        if isinstance(nome_tipo, str) and nome_tipo.strip().upper() == "CNH":
                            name_ok = True
                except Exception:
                    pass
                if not name_ok:
                    try:
                        if getattr(d, "nome", "").strip().upper() == "CNH":
                            name_ok = True
                    except Exception:
                        pass
                if not name_ok:
                    continue

                # pega a validade no doc
                for a in ("validade", "data_validade", "vencimento", "expira_em"):
                    if hasattr(d, a):
                        vv = getattr(d, a)
                        if vv:
                            return vv
    except Exception:
        pass

    return None

def _is_driver(emp):
    # considera Motorista por relação Funcao ou por texto no campo
    try:
        func = getattr(emp, "funcao", None)
        nome = getattr(func, "nome", None)
        if isinstance(nome, str) and nome.strip().lower() == "motorista":
            return True
    except Exception:
        pass
    # fallback: campos de texto
    for a in ("cargo", "funcao_nome", "role_name"):
        if hasattr(emp, a):
            val = getattr(emp, a)
            if isinstance(val, str) and val.strip().lower() == "motorista":
                return True
    return False

@main_bp.route("/api/cnh-stats", endpoint="cnh_stats")
@login_required
def cnh_stats():
    # horizonte configurável (dias) para "a vencer"
    horizon_days = int(os.getenv("CNH_ALERT_DAYS", "30"))
    today = date.today()
    deadline = today + timedelta(days=horizon_days)

    # busca todos e filtra em Python para robustez
    emps = Employee.query.all()
    drivers = [e for e in emps if _is_driver(e)]

    vencidas = 0
    a_vencer = 0

    for e in drivers:
        dt = _get_cnh_expiration(e)
        if not dt:
            continue
        if isinstance(dt, datetime):
            dt = dt.date()
        # se vier string "YYYY-MM-DD"
        if isinstance(dt, str):
            try:
                dt = date.fromisoformat(dt[:10])
            except Exception:
                continue

        try:
            if dt < today:
                vencidas += 1
            elif dt <= deadline:
                a_vencer += 1
        except Exception:
            # em caso de tipos estranhos, ignora
            continue

    return jsonify({
        "cnh_vencidas": vencidas,
        "cnh_a_vencer": a_vencer,
        "horizon_days": horizon_days
    })
