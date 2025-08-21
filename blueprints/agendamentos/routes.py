# blueprints/agendamentos/routes.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import agendamentos_bp
from models import db, Servico, Agendamento, Customer, Company
from forms import ServicoForm, AgendamentoForm
from datetime import datetime

# ... (código do _get_company_header e das rotas de serviço continua igual) ...
def _get_company_header():
    try:
        c = Company.query.filter_by(is_default=True).first()
        if not c: c = Company.query.order_by(Company.id.asc()).first()
        if c: return { "nome": c.nome_fantasia or c.razao_social or "", "endereco": f"{c.logradouro or ''}, {c.numero or ''} - {c.cidade or ''}", "cnpj": c.cnpj or "" }
    except Exception: pass
    return { "nome": "Empresa Não Configurada", "endereco": "", "cnpj": "" }

@agendamentos_bp.route('/')
@login_required
def index():
    return render_template("agendamentos/index.html")

@agendamentos_bp.route('/servicos')
@login_required
def servico_list():
    servicos = Servico.query.order_by(Servico.nome).all()
    return render_template('agendamentos/servico_list.html', items=servicos)

@agendamentos_bp.route('/servicos/novo', methods=['GET', 'POST'])
@login_required
def servico_new():
    form = ServicoForm()
    if form.validate_on_submit():
        novo_servico = Servico(nome=form.nome.data)
        db.session.add(novo_servico); db.session.commit()
        flash('Serviço cadastrado com sucesso!', 'success')
        return redirect(url_for('agendamentos.servico_list'))
    return render_template('agendamentos/servico_form.html', form=form, title='Novo Serviço')

@agendamentos_bp.route('/servicos/<int:servico_id>/editar', methods=['GET', 'POST'])
@login_required
def servico_edit(servico_id):
    servico = Servico.query.get_or_404(servico_id)
    form = ServicoForm(obj=servico)
    if form.validate_on_submit():
        servico.nome = form.nome.data
        db.session.commit()
        flash('Serviço atualizado com sucesso!', 'success')
        return redirect(url_for('agendamentos.servico_list'))
    return render_template('agendamentos/servico_form.html', form=form, title='Editar Serviço')

@agendamentos_bp.route('/servicos/<int:servico_id>/excluir', methods=['POST'])
@login_required
def servico_delete(servico_id):
    servico = Servico.query.get_or_404(servico_id)
    db.session.delete(servico); db.session.commit()
    flash('Serviço excluído com sucesso.', 'success')
    return redirect(url_for('agendamentos.servico_list'))

@agendamentos_bp.route('/lista')
@login_required
def agendamento_list():
    agendamentos = Agendamento.query.order_by(Agendamento.data_hora.desc()).all()
    return render_template('agendamentos/agendamento_list.html', items=agendamentos)

# --- FUNÇÃO DE SALVAR CORRIGIDA E MELHORADA ---
def _save_agendamento(form, agendamento=None):
    if not agendamento:
        agendamento = Agendamento()
    
    servico = Servico.query.get(form.servico_id.data)
    customer_id = form.customer_id.data if form.customer_id.data != 0 else None
    visitante_nome = (form.visitante_nome.data or "").strip()

    if servico and servico.nome.strip().lower() == 'visita':
        if not visitante_nome:
            flash("Para o serviço 'Visita', o nome do visitante é obrigatório.", 'danger')
            return None, False
        agendamento.customer_id = None
        agendamento.visitante_nome = visitante_nome
    else:
        if not customer_id:
            flash("Para este serviço, é obrigatório selecionar um cliente.", 'danger')
            return None, False
        agendamento.customer_id = customer_id
        agendamento.visitante_nome = None

    agendamento.servico_id = form.servico_id.data
    agendamento.data_hora = form.data_hora.data
    agendamento.local = form.local.data
    agendamento.observacao = form.observacao.data
    agendamento.status = form.status.data

    if not agendamento.id:
        db.session.add(agendamento)
    
    db.session.commit()
    return agendamento, True

@agendamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def agendamento_new():
    form = AgendamentoForm()
    form.customer_id.choices = [(c.id, c.nome_razao_social) for c in Customer.query.order_by(Customer.nome_razao_social).all()]
    form.servico_id.choices = [(s.id, s.nome) for s in Servico.query.order_by(Servico.nome).all()]
    
    if form.validate_on_submit():
        agendamento, sucesso = _save_agendamento(form)
        if sucesso:
            flash('Agendamento criado com sucesso!', 'success')
            if form.submit_and_print.data:
                return redirect(url_for('agendamentos.imprimir_agendamento', agendamento_id=agendamento.id))
            else:
                return redirect(url_for('agendamentos.agendamento_list'))
            
    return render_template('agendamentos/agendamento_form.html', form=form, title='Novo Agendamento')

@agendamentos_bp.route('/<int:agendamento_id>/editar', methods=['GET', 'POST'])
@login_required
def agendamento_edit(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    form = AgendamentoForm(obj=agendamento)
    form.customer_id.choices = [(c.id, c.nome_razao_social) for c in Customer.query.order_by(Customer.nome_razao_social).all()]
    form.servico_id.choices = [(s.id, s.nome) for s in Servico.query.order_by(Servico.nome).all()]

    if form.validate_on_submit():
        agendamento, sucesso = _save_agendamento(form, agendamento)
        if sucesso:
            flash('Agendamento atualizado com sucesso!', 'success')
            if form.submit_and_print.data:
                return redirect(url_for('agendamentos.imprimir_agendamento', agendamento_id=agendamento.id))
            else:
                return redirect(url_for('agendamentos.agendamento_list'))
            
    return render_template('agendamentos/agendamento_form.html', form=form, title='Editar Agendamento')

@agendamentos_bp.route('/<int:agendamento_id>/excluir', methods=['POST'])
@login_required
def agendamento_delete(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    db.session.delete(agendamento); db.session.commit()
    flash('Agendamento excluído com sucesso.', 'success')
    return redirect(url_for('agendamentos.agendamento_list'))

@agendamentos_bp.route('/imprimir/<int:agendamento_id>')
@login_required
def imprimir_agendamento(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    empresa = _get_company_header()
    return render_template("agendamentos/recibo_agendamento.html", agendamento=agendamento, empresa=empresa)