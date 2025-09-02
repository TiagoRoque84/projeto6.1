# blueprints/dash/routes.py

from flask import Blueprint, render_template
from flask_login import login_required
from models import Document, Employee, Agendamento, Proposal, Vehicle, MaintenanceLog
from datetime import date, timedelta, datetime
from sqlalchemy import desc

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

    # Agendamentos
    agendamentos_atrasados_list = Agendamento.query.filter(Agendamento.data_hora < agora, Agendamento.status == 'Agendado').order_by(Agendamento.data_hora.asc()).all()
    em_7_dias = agora + timedelta(days=7)
    agendamentos_proximos_list = Agendamento.query.filter(Agendamento.data_hora >= agora, Agendamento.data_hora <= em_7_dias, Agendamento.status == 'Agendado').order_by(Agendamento.data_hora.asc()).all()
    
    # Orçamentos
    pending_proposals = Proposal.query.filter_by(status='Pendente').count()

    # Contagem geral
    total_func = Employee.query.count()
    ativos = Employee.query.filter_by(ativo=True).count()
    inativos = total_func - ativos

    # --- INÍCIO: NOVAS QUERIES PARA FROTA ---
    licenc_venc_list = Vehicle.query.filter(Vehicle.venc_licenciamento < hoje).order_by(Vehicle.venc_licenciamento.asc()).all()
    licenc_avencer_list = Vehicle.query.filter(Vehicle.venc_licenciamento >= hoje, Vehicle.venc_licenciamento <= em_30).order_by(Vehicle.venc_licenciamento.asc()).all()
    
    # Para a troca de óleo, vamos pegar o último registro de cada veículo
    veiculos_oleo_avencer = []
    # Um valor de "alerta" de KM, ex: 1000km antes do vencimento
    KM_ALERTA_OLEO = 1000 
    for v in Vehicle.query.all():
        last_log = v.manutencoes.first()
        if last_log and last_log.km_atual and last_log.km_proxima_troca:
            if last_log.km_atual >= last_log.km_proxima_troca - KM_ALERTA_OLEO:
                veiculos_oleo_avencer.append(v)
    # --- FIM: NOVAS QUERIES ---

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
        licenc_venc_list=licenc_venc_list, # NOVO
        licenc_avencer_list=licenc_avencer_list, # NOVO
        veiculos_oleo_avencer=veiculos_oleo_avencer, # NOVO
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
        pending_proposals=pending_proposals,
        total_func=total_func,
        ativos=ativos,
        inativos=inativos,
        licenc_venc=len(licenc_venc_list), # NOVO
        licenc_avencer=len(licenc_avencer_list), # NOVO
        oleo_avencer=len(veiculos_oleo_avencer) # NOVO
    )