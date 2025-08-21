# blueprints/agendamentos/routes.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import agendamentos_bp
from models import db, Servico, Agendamento, Customer
from forms import ServicoForm, AgendamentoForm
from datetime import datetime

# --- TELA PRINCIPAL DO MÓDULO DE AGENDAMENTOS ---
@agendamentos_bp.route('/')
@login_required
def index():
    """Renderiza o menu principal do módulo de Agendamentos."""
    return render_template("agendamentos/index.html")

# --- ROTAS PARA CADASTRO DE SERVIÇOS ---

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
        db.session.add(novo_servico)
        db.session.commit()
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
    db.session.delete(servico)
    db.session.commit()
    flash('Serviço excluído com sucesso.', 'success')
    return redirect(url_for('agendamentos.servico_list'))

# --- INÍCIO: ROTAS PARA AGENDAMENTOS ---

@agendamentos_bp.route('/lista')
@login_required
def agendamento_list():
    """Exibe a lista de agendamentos, dos mais recentes para os mais antigos."""
    agendamentos = Agendamento.query.order_by(Agendamento.data_hora.desc()).all()
    return render_template('agendamentos/agendamento_list.html', items=agendamentos)

@agendamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def agendamento_new():
    """Formulário para criar um novo agendamento."""
    form = AgendamentoForm()
    # Popula os campos de seleção (dropdowns)
    form.customer_id.choices = [(c.id, c.nome_razao_social) for c in Customer.query.order_by(Customer.nome_razao_social).all()]
    form.servico_id.choices = [(s.id, s.nome) for s in Servico.query.order_by(Servico.nome).all()]
    
    if form.validate_on_submit():
        novo_agendamento = Agendamento(
            customer_id=form.customer_id.data,
            servico_id=form.servico_id.data,
            data_hora=form.data_hora.data,
            local=form.local.data,
            observacao=form.observacao.data,
            status=form.status.data
        )
        db.session.add(novo_agendamento)
        db.session.commit()
        flash('Agendamento criado com sucesso!', 'success')
        return redirect(url_for('agendamentos.agendamento_list'))
        
    return render_template('agendamentos/agendamento_form.html', form=form, title='Novo Agendamento')

@agendamentos_bp.route('/<int:agendamento_id>/editar', methods=['GET', 'POST'])
@login_required
def agendamento_edit(agendamento_id):
    """Formulário para editar um agendamento."""
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    form = AgendamentoForm(obj=agendamento)
    form.customer_id.choices = [(c.id, c.nome_razao_social) for c in Customer.query.order_by(Customer.nome_razao_social).all()]
    form.servico_id.choices = [(s.id, s.nome) for s in Servico.query.order_by(Servico.nome).all()]

    if form.validate_on_submit():
        form.populate_obj(agendamento)
        db.session.commit()
        flash('Agendamento atualizado com sucesso!', 'success')
        return redirect(url_for('agendamentos.agendamento_list'))
        
    return render_template('agendamentos/agendamento_form.html', form=form, title='Editar Agendamento')

@agendamentos_bp.route('/<int:agendamento_id>/excluir', methods=['POST'])
@login_required
def agendamento_delete(agendamento_id):
    """Rota para excluir um agendamento."""
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    db.session.delete(agendamento)
    db.session.commit()
    flash('Agendamento excluído com sucesso.', 'success')
    return redirect(url_for('agendamentos.agendamento_list'))

# --- FIM: ROTAS PARA AGENDAMENTOS ---