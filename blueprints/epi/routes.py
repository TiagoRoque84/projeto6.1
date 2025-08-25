# blueprints/epi/routes.py
import io
import os
from flask import render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required
from . import epi_bp
from models import db, Fornecedor, EPI, MovimentacaoEPI, Employee, EmployeeDocument, EPISaida
from forms import FornecedorForm, EPIForm, EPIEntradaForm, EPISaidaForm
from pdf_reports import epi_saida_pdf, epi_summary_pdf 
from datetime import datetime, date
from werkzeug.utils import secure_filename

@epi_bp.route('/')
@login_required
def index():
    return render_template("epi/index.html")

@epi_bp.route('/fornecedores')
@login_required
def fornecedor_list():
    fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()
    return render_template('epi/fornecedor_list.html', items=fornecedores)

@epi_bp.route('/fornecedores/novo', methods=['GET', 'POST'])
@login_required
def fornecedor_new():
    form = FornecedorForm()
    if form.validate_on_submit():
        novo_fornecedor = Fornecedor(nome=form.nome.data, cnpj=form.cnpj.data)
        db.session.add(novo_fornecedor); db.session.commit()
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
    db.session.delete(fornecedor); db.session.commit()
    flash('Fornecedor excluído com sucesso.', 'success')
    return redirect(url_for('epi.fornecedor_list'))

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
        db.session.add(novo_epi); db.session.commit()
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
    db.session.delete(epi); db.session.commit()
    flash('EPI excluído com sucesso.', 'success')
    return redirect(url_for('epi.epi_list'))

@epi_bp.route('/movimentacoes')
@login_required
def movimentacao_list():
    movimentacoes = MovimentacaoEPI.query.order_by(MovimentacaoEPI.data_movimentacao.desc()).all()
    saidas = EPISaida.query.order_by(EPISaida.data_saida.desc()).all()
    return render_template('epi/movimentacao_list.html', items=movimentacoes, saidas=saidas)

@epi_bp.route('/entrada', methods=['GET', 'POST'])
@login_required
def entrada_new():
    form = EPIEntradaForm()
    form.epi_id.choices = [(e.id, f"{e.nome} (Estoque atual: {e.estoque})") for e in EPI.query.order_by(EPI.nome).all()]
    if form.validate_on_submit():
        epi = EPI.query.get_or_404(form.epi_id.data)
        quantidade = form.quantidade.data
        nova_movimentacao = MovimentacaoEPI(epi_id=epi.id, tipo='ENTRADA', quantidade=quantidade, retirado_por='ENTRADA NO ESTOQUE')
        db.session.add(nova_movimentacao)
        epi.estoque += quantidade
        db.session.commit()
        flash(f'{quantidade} unidade(s) de "{epi.nome}" adicionada(s) ao estoque.', 'success')
        return redirect(url_for('epi.movimentacao_list'))
    return render_template('epi/entrada_form.html', form=form, title='Registrar Entrada de EPI')

@epi_bp.route('/saida', methods=['GET', 'POST'])
@login_required
def saida_new():
    form = EPISaidaForm()
    
    # Preenche as opções para o dropdown de funcionários
    form.employee_id.choices = [(0, 'Selecionar funcionário...')] + [(emp.id, emp.nome) for emp in Employee.query.filter_by(ativo=True).order_by(Employee.nome).all()]
    
    # Preenche as opções de EPIs para o dropdown dentro do formulário dinâmico
    epi_choices = [(e.id, f"{e.nome} (Estoque: {e.estoque})") for e in EPI.query.order_by(EPI.nome).all()]
    for item_form in form.items:
        item_form.epi_id.choices = epi_choices

    if form.validate_on_submit():
        employee_id = form.employee_id.data if form.employee_id.data != 0 else None
        retirado_por_terceiro = form.retirado_por_terceiro.data.strip()

        if not employee_id and not retirado_por_terceiro:
            flash('É necessário selecionar um funcionário ou informar o nome do terceiro.', 'danger')
            return render_template('epi/saida_form.html', form=form, title='Registrar Retirada de EPI', epi_choices_json=epi_choices)

        # Validação de estoque antes de salvar
        for item_data in form.items.data:
            epi = EPI.query.get(item_data['epi_id'])
            if not epi or epi.estoque < item_data['quantidade']:
                flash(f'Estoque insuficiente para "{epi.nome}". Disponível: {epi.estoque}.', 'danger')
                return render_template('epi/saida_form.html', form=form, title='Registrar Retirada de EPI', epi_choices_json=epi_choices)

        retirado_por_nome = retirado_por_terceiro
        if employee_id:
            employee = Employee.query.get(employee_id)
            retirado_por_nome = employee.nome

        # Cria a 'Saida' principal
        nova_saida = EPISaida(employee_id=employee_id, retirado_por=retirado_por_nome)
        db.session.add(nova_saida)
        
        # Cria as movimentações individuais para cada item
        for item_data in form.items.data:
            epi = EPI.query.get(item_data['epi_id'])
            quantidade = item_data['quantidade']
            
            mov = MovimentacaoEPI(
                epi_id=epi.id,
                tipo='SAIDA',
                quantidade=quantidade,
                saida=nova_saida # Vincula o item à saida principal
            )
            db.session.add(mov)
            epi.estoque -= quantidade
        
        db.session.commit()
        
        # Gera o PDF
        pdf_buffer = io.BytesIO()
        epi_saida_pdf(pdf_buffer, current_app, nova_saida)
        pdf_buffer.seek(0)
        
        # Salva o PDF nos documentos do funcionário, se aplicável
        if employee_id:
            try:
                subdir = "func_docs"
                filename = secure_filename(f"comprovante_epi_{nova_saida.id}_{date.today().isoformat()}.pdf")
                upload_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], subdir)
                os.makedirs(upload_dir, exist_ok=True)
                
                filepath = os.path.join(upload_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(pdf_buffer.read())
                pdf_buffer.seek(0)

                novo_documento = EmployeeDocument(
                    employee_id=employee_id,
                    tipo="Comprovante de EPI",
                    descricao=f"Retirada de {len(form.items.data)} tipo(s) de EPI.",
                    arquivo_path=os.path.join(subdir, filename).replace("\\", "/")
                )
                db.session.add(novo_documento)
                db.session.commit()
                flash(f"Comprovante salvo nos documentos de {employee.nome}.", "info")
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao salvar comprovante: {e}", "danger")
        
        return send_file(pdf_buffer, as_attachment=True, download_name=f'comprovante_epi_{nova_saida.id}.pdf', mimetype='application/pdf')

    return render_template('epi/saida_form.html', form=form, title='Registrar Retirada de EPI', epi_choices_json=epi_choices)


@epi_bp.route('/movimentacoes/relatorio')
@login_required
def relatorio_epi():
    start_date_str = request.args.get('data_inicio')
    end_date_str = request.args.get('data_fim')

    if not start_date_str or not end_date_str:
        flash("Por favor, selecione a data de início e a data de fim para o relatório.", "danger")
        return redirect(url_for('epi.movimentacao_list'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Formato de data inválido.", "danger")
        return redirect(url_for('epi.movimentacao_list'))

    start_of_day = datetime.combine(start_date, datetime.min.time())
    end_of_day = datetime.combine(end_date, datetime.max.time())
    
    movements = MovimentacaoEPI.query.filter(
        MovimentacaoEPI.data_movimentacao >= start_of_day,
        MovimentacaoEPI.data_movimentacao <= end_of_day
    ).order_by(MovimentacaoEPI.data_movimentacao.asc()).all()

    if not movements:
        flash(f"Nenhuma movimentação de EPI encontrada para o período de {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}.", "info")
        return redirect(url_for('epi.movimentacao_list'))

    buffer = io.BytesIO()
    epi_summary_pdf(buffer, None, movements, start_date, end_date)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'relatorio_epi_{start_date.strftime("%Y-%m-%d")}_a_{end_date.strftime("%Y-%m-%d")}.pdf',
        mimetype='application/pdf'
    )

@epi_bp.route('/reimprimir_retirada/<int:saida_id>')
@login_required
def reimprimir_retirada(saida_id):
    saida = EPISaida.query.get_or_404(saida_id)
    buffer = io.BytesIO()
    epi_saida_pdf(buffer, current_app, saida)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'comprovante_epi_{saida.id}.pdf',
        mimetype='application/pdf'
    )