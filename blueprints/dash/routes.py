
from flask import Blueprint, render_template
from flask_login import login_required
from models import Document, Employee
from datetime import date, timedelta

dash_bp = Blueprint("dash", __name__, template_folder='../../templates')

@dash_bp.route("/dash")
@login_required
def dashboard():
    hoje = date.today(); em_30 = hoje + timedelta(days=30)
    docs_venc = Document.query.filter(Document.data_vencimento != None, Document.data_vencimento < hoje).count()
    docs_avencer = Document.query.filter(Document.data_vencimento != None, Document.data_vencimento >= hoje, Document.data_vencimento <= em_30).count()
    aso_venc = Employee.query.filter(Employee.aso_validade != None, Employee.aso_validade < hoje).count()
    aso_avencer = Employee.query.filter(Employee.aso_validade != None, Employee.aso_validade >= hoje, Employee.aso_validade <= em_30).count()
    tox_venc = Employee.query.filter(Employee.exame_toxico_validade != None, Employee.exame_toxico_validade < hoje).count()
    tox_avencer = Employee.query.filter(Employee.exame_toxico_validade != None, Employee.exame_toxico_validade >= hoje, Employee.exame_toxico_validade <= em_30).count()
    total_func = Employee.query.count()
    ativos = Employee.query.filter_by(ativo=True).count()
    inativos = total_func - ativos
    return render_template("dashboard.html",
        docs_venc=docs_venc, docs_avencer=docs_avencer,
        aso_venc=aso_venc, aso_avencer=aso_avencer,
        tox_venc=tox_venc, tox_avencer=tox_avencer,
        total_func=total_func, ativos=ativos, inativos=inativos)
