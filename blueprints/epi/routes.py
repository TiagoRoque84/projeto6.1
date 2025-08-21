# blueprints/epi/routes.py
import io
from flask import render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required
from . import epi_bp
from models import db, Fornecedor, EPI, MovimentacaoEPI, Employee
from forms import FornecedorForm, EPIForm, EPIEntradaForm, EPISaidaForm
from pdf_reports import epi_saida_pdf

# --- TELA PRINCIPAL DO MÓDULO DE EPI ---
@epi_bp.route('/')
@login_required
def index():
    """Renderiza o menu principal do módulo de EPIs."""
    return render_template("epi/index.html")

# --- ROTAS PARA FORNECEDORES ---
@epi_bp.route('/fornecedores')
@login_required
def fornecedor_list():
    """Lista todos os fornecedores."""
    fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()
    return render_template('epi/fornecedor_list.html', items=fornecedores)

@epi_bp.route('/fornecedores/novo', methods=['GET', 'POST'])
@login_required
def fornecedor_new():
    form = FornecedorForm()
    if form.validate_on_submit():
        novo_fornecedor = Fornecedor(nome=form.nome.data, cnpj=form.cnpj.data)
        db.session.add(novo_fornecedor)
        db.session.commit()
        flash('Fornecedor cadastrado com sucesso!', 'success')
        return redirect(url_for('epi.fornecedor_list'))
    return render_template('epi/fornecedor_form.html', form=form, title='Novo Fornecedor')

@epi_bp.route('/fornecedores/<int:fornecedor_id>/editar', methods=['GET', 'POST'])
@login_required
def fornecedor_edit(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
    form = FornecedorForm(obj=fornecedor)
    if form.validate_on_submit():
        fornecedor.nome = form.nome.data
        fornecedor.cnpj = form.cnpj.data
        db.session.commit()
        flash('Fornecedor atualizado com sucesso!', 'success')
        return redirect(url_for('epi.fornecedor_list'))
    return render_template('epi/fornecedor_form.html', form=form, title='Editar Fornecedor')

@epi_bp.route('/fornecedores/<int:fornecedor_id>/excluir', methods=['POST'])
@login_required
def fornecedor_delete(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
    db.session.delete(fornecedor)
    db.session.commit()
    flash('Fornecedor excluído com sucesso.', 'success')
    return redirect(url_for('epi.fornecedor_list'))

# --- ROTAS PARA CADASTRO DE EPIs ---
@epi_bp.route('/epis')
@login_required
def epi_list():
    epis = EPI.query.order_by(EPI.nome).all()
    return render_template('epi/epi_list.html', items=epis)

@epi_bp.route('/epis/novo', methods=['GET', 'POST'])
@login_required
def epi_new():
    form = EPIForm()
    form.fornecedor_id.choices = [(0, 'Nenhum')] + [(f.id, f.nome) for f in Fornecedor.query.order_by(Fornecedor.nome).all()]
    if form.validate_on_submit():
        fornecedor_id = form.fornecedor_id.data if form.fornecedor_id.data != 0 else None
        novo_epi = EPI(nome=form.nome.data, ca=form.ca.data, fornecedor_id=fornecedor_id)
        db.session.add(novo_epi)
        db.session.commit()
        flash('EPI cadastrado com sucesso!', 'success')
        return redirect(url_for('epi.epi_list'))
    return render_template('epi/epi_form.html', form=form, title='Novo EPI')

@epi_bp.route('/epis/<int:epi_id>/editar', methods=['GET', 'POST'])
@login_required
def epi_edit(epi_id):
    epi = EPI.query.get_or_404(epi_id)
    form = EPIForm(obj=epi)
    form.fornecedor_id.choices = [(0, 'Nenhum')] + [(f.id, f.nome) for f in Fornecedor.query.order_by(Fornecedor.nome).all()]
    if form.validate_on_submit():
        epi.nome = form.nome.data
        epi.ca = form.ca.data
        epi.fornecedor_id = form.fornecedor_id.data if form.fornecedor_id.data != 0 else None
        db.session.commit()
        flash('EPI atualizado com sucesso!', 'success')
        return redirect(url_for('epi.epi_list'))
    return render_template('epi/epi_form.html', form=form, title='Editar EPI')

@epi_bp.route('/epis/<int:epi_id>/excluir', methods=['POST'])
@login_required
def epi_delete(epi_id):
    epi = EPI.query.get_or_404(epi_id)
    db.session.delete(epi)
    db.session.commit()
    flash('EPI excluído com sucesso.', 'success')
    return redirect(url_for('epi.epi_list'))

# --- INÍCIO: NOVAS ROTAS DE MOVIMENTAÇÃO DE ESTOQUE ---

@epi_bp.route('/movimentacoes')
@login_required
def movimentacao_list():
    """Exibe o histórico de todas as entradas e saídas."""
    movimentacoes = MovimentacaoEPI.query.order_by(MovimentacaoEPI.data_movimentacao.desc()).all()
    return render_template('epi/movimentacao_list.html', items=movimentacoes)

@epi_bp.route('/entrada', methods=['GET', 'POST'])
@login_required
def entrada_new():
    """Formulário para registrar entrada de EPIs no estoque."""
    form = EPIEntradaForm()
    form.epi_id.choices = [(e.id, f"{e.nome} (Estoque atual: {e.estoque})") for e in EPI.query.order_by(EPI.nome).all()]
    
    if form.validate_on_submit():
        epi = EPI.query.get_or_404(form.epi_id.data)
        quantidade = form.quantidade.data
        
        # Cria o registro da movimentação
        nova_movimentacao = MovimentacaoEPI(
            epi_id=epi.id,
            tipo='ENTRADA',
            quantidade=quantidade,
            retirado_por='ENTRADA NO ESTOQUE' # Informação padrão para entradas
        )
        db.session.add(nova_movimentacao)
        
        # Atualiza o estoque do EPI
        epi.estoque += quantidade
        
        db.session.commit()
        flash(f'{quantidade} unidade(s) de "{epi.nome}" adicionada(s) ao estoque.', 'success')
        return redirect(url_for('epi.movimentacao_list'))

    return render_template('epi/entrada_form.html', form=form, title='Registrar Entrada de EPI')

@epi_bp.route('/saida', methods=['GET', 'POST'])
@login_required
def saida_new():
    """Formulário para registrar a retirada de EPIs por um funcionário."""
    form = EPISaidaForm()
    # Popula os selects do formulário
    form.epi_id.choices = [(e.id, f"{e.nome} (Estoque: {e.estoque})") for e in EPI.query.order_by(EPI.nome).all()]
    form.employee_id.choices = [(0, 'Selecionar funcionário...')] + [(emp.id, emp.nome) for emp in Employee.query.filter_by(ativo=True).order_by(Employee.nome).all()]

    if form.validate_on_submit():
        epi = EPI.query.get_or_404(form.epi_id.data)
        quantidade = form.quantidade.data
        employee_id = form.employee_id.data if form.employee_id.data != 0 else None
        retirado_por_terceiro = form.retirado_por_terceiro.data.strip()

        # Validações
        if not employee_id and not retirado_por_terceiro:
            flash('É necessário selecionar um funcionário ou informar o nome do terceiro.', 'danger')
            return render_template('epi/saida_form.html', form=form, title='Registrar Retirada de EPI')
        
        if epi.estoque < quantidade:
            flash(f'Estoque insuficiente para "{epi.nome}". Disponível: {epi.estoque}.', 'danger')
            return render_template('epi/saida_form.html', form=form, title='Registrar Retirada de EPI')

        # Define quem retirou
        retirado_por_nome = ""
        employee = None
        if employee_id:
            employee = Employee.query.get(employee_id)
            retirado_por_nome = employee.nome
        else:
            retirado_por_nome = retirado_por_terceiro

        # Cria o registro da movimentação
        nova_movimentacao = MovimentacaoEPI(
            epi_id=epi.id,
            tipo='SAIDA',
            quantidade=quantidade,
            retirado_por=retirado_por_nome,
            employee_id=employee_id
        )
        db.session.add(nova_movimentacao)
        
        # Atualiza o estoque
        epi.estoque -= quantidade
        
        db.session.commit()
        
        # Gera o PDF
        buffer = io.BytesIO()
        epi_saida_pdf(buffer, current_app, nova_movimentacao)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'comprovante_epi_{nova_movimentacao.id}.pdf',
            mimetype='application/pdf'
        )

    return render_template('epi/saida_form.html', form=form, title='Registrar Retirada de EPI')

# --- FIM: NOVAS ROTAS DE MOVIMENTAÇÃO DE ESTOQUE ---