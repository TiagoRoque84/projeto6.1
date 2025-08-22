# blueprints/dash/routes.py

from flask import Blueprint, render_template
from flask_login import login_required
from models import Document, Employee, Agendamento, Proposal
from datetime import date, timedelta, datetime

dash_bp = Blueprint("dash", __name__, template_folder='../../templates')

@dash_bp.route("/dash")
@login_required
def dashboard():
    hoje = date.today()
    agora = datetime.now()
    em_30 = hoje + timedelta(days=30)

    # Documentos da Empresa
    docs_venc_list = Document.query.filter(Document.data_vencimento < hoje).order_by(Document.data_vencimento.asc()).all()
    docs_avencer_list = Document.query.filter(Document.data_vencimento >= hoje, Document.data_vencimento <= em_30).order_by(Document.data_vencimento.asc()).all()

    # Documentos de Funcionários
    aso_venc_list = Employee.query.filter(Employee.aso_validade < hoje, Employee.ativo==True).order_by(Employee.aso_validade.asc()).all()
    aso_avencer_list = Employee.query.filter(Employee.aso_validade >= hoje, Employee.aso_validade <= em_30, Employee.ativo==True).order_by(Employee.aso_validade.asc()).all()
    
    cnh_venc_list = Employee.query.filter(Employee.cnh_validade < hoje, Employee.ativo==True).order_by(Employee.cnh_validade.asc()).all()
    cnh_avencer_list = Employee.query.filter(Employee.cnh_validade >= hoje, Employee.cnh_validade <= em_30, Employee.ativo==True).order_by(Employee.cnh_validade.asc()).all()

    tox_venc_list = Employee.query.filter(Employee.exame_toxico_validade < hoje, Employee.ativo==True).order_by(Employee.exame_toxico_validade.asc()).all()
    tox_avencer_list = Employee.query.filter(Employee.exame_toxico_validade >= hoje, Employee.exame_toxico_validade <= em_30, Employee.ativo==True).order_by(Employee.exame_toxico_validade.asc()).all()

    # --- INÍCIO: NOVAS QUERIES PARA AGENDAMENTOS ---
    agendamentos_atrasados_list = Agendamento.query.filter(Agendamento.data_hora < agora, Agendamento.status == 'Agendado').order_by(Agendamento.data_hora.asc()).all()
    em_7_dias = agora + timedelta(days=7)
    agendamentos_proximos_list = Agendamento.query.filter(Agendamento.data_hora >= agora, Agendamento.data_hora <= em_7_dias, Agendamento.status == 'Agendado').order_by(Agendamento.data_hora.asc()).all()
    
    # Adicionado para Orçamentos
    pending_proposals = Proposal.query.filter_by(status='Pendente').count()

    # Contagem geral
    total_func = Employee.query.count()
    ativos = Employee.query.filter_by(ativo=True).count()
    inativos = total_func - ativos

    return render_template("dashboard.html",
        # Listas para os modais
        docs_venc_list=docs_venc_list,
        docs_avencer_list=docs_avencer_list,
        aso_venc_list=aso_venc_list,
        aso_avencer_list=aso_avencer_list,
        cnh_venc_list=cnh_venc_list,
        cnh_avencer_list=cnh_avencer_list,
        tox_venc_list=tox_venc_list,
        tox_avencer_list=tox_avencer_list,
        agendamentos_atrasados_list=agendamentos_atrasados_list,
        agendamentos_proximos_list=agendamentos_proximos_list,
        # Contagens para os cards
        docs_venc=len(docs_venc_list),
        docs_avencer=len(docs_avencer_list),
        aso_venc=len(aso_venc_list),
        aso_avencer=len(aso_avencer_list),
        cnh_venc=len(cnh_venc_list),
        cnh_avencer=len(cnh_avencer_list),
        tox_venc=len(tox_venc_list),
        tox_avencer=len(tox_avencer_list),
        agendamentos_atrasados=len(agendamentos_atrasados_list),
        agendamentos_proximos=len(agendamentos_proximos_list),
        pending_proposals=pending_proposals, # Adicionado
        total_func=total_func,
        ativos=ativos,
        inativos=inativos
    )