# blueprints/proposals/routes.py
import io
from flask import render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required
from . import proposals_bp
from models import db, Proposal, Company, Customer, ProposalItem
from forms import ProposalForm
from pdf_reports import proposal_pdf

@proposals_bp.route('/')
@login_required
def list():
    status = request.args.get('status', '').strip()
    query = Proposal.query.order_by(Proposal.created_at.desc())
    if status:
        query = query.filter(Proposal.status == status)
    
    items = query.all()
    return render_template('proposals/list.html', items=items, current_status=status)

def _process_form_and_save(form, proposal=None):
    """Função central para criar ou editar um orçamento."""
    if not proposal:
        proposal = Proposal()
        db.session.add(proposal)

    # Popula os campos principais do orçamento
    proposal.issuing_company_id = form.issuing_company_id.data
    proposal.customer_id = form.customer_id.data
    proposal.attention = form.attention.data
    proposal.representative_name = form.representative_name.data
    proposal.status = form.status.data

    # Remove os itens antigos para substituí-los pelos novos do formulário
    for item in proposal.items:
        db.session.delete(item)
    
    # Adiciona os novos itens
    for item_form in form.items:
        item = ProposalItem(
            description=item_form.description.data,
            unit=item_form.unit.data,
            value=item_form.value.data
        )
        proposal.items.append(item)
    
    db.session.commit()

@proposals_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def new():
    form = ProposalForm()
    # Filtra para mostrar apenas as empresas que você indicou
    form.issuing_company_id.choices = [(c.id, c.nome_fantasia or c.razao_social) for c in Company.query.filter(Company.razao_social.like('%RADDI%') | Company.razao_social.like('%EZIO%')).order_by(Company.nome_fantasia).all()]
    form.customer_id.choices = [(c.id, c.nome_razao_social) for c in Customer.query.order_by(Customer.nome_razao_social).all()]

    if form.validate_on_submit():
        _process_form_and_save(form)
        flash('Orçamento criado com sucesso!', 'success')
        return redirect(url_for('proposals.list'))
        
    return render_template('proposals/form.html', form=form, title='Novo Orçamento')

@proposals_bp.route('/<int:proposal_id>/editar', methods=['GET', 'POST'])
@login_required
def edit(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    form = ProposalForm(obj=proposal)
    form.issuing_company_id.choices = [(c.id, c.nome_fantasia or c.razao_social) for c in Company.query.order_by(Company.nome_fantasia).all()]
    form.customer_id.choices = [(c.id, c.nome_razao_social) for c in Customer.query.order_by(Customer.nome_razao_social).all()]

    if form.validate_on_submit():
        _process_form_and_save(form, proposal)
        flash('Orçamento atualizado com sucesso!', 'success')
        return redirect(url_for('proposals.list'))

    return render_template('proposals/form.html', form=form, title='Editar Orçamento')

@proposals_bp.route('/<int:proposal_id>/pdf')
@login_required
def pdf(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    buffer = io.BytesIO()
    proposal_pdf(buffer, current_app, proposal)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'orcamento_{proposal.id}_{proposal.customer.nome_razao_social}.pdf',
        mimetype='application/pdf'
    )

@proposals_bp.route('/<int:proposal_id>/excluir', methods=['POST'])
@login_required
def delete(proposal_id):
    proposal = Proposal.query.get_or_404(proposal_id)
    try:
        db.session.delete(proposal)
        db.session.commit()
        flash('Orçamento excluído com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir o orçamento: {e}', 'danger')
    return redirect(url_for('proposals.list'))