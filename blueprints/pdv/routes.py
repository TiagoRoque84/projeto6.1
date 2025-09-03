# blueprints/pdv/routes.py

import os
import io
from decimal import Decimal
from flask import request, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from . import pdv_bp
from datetime import datetime, date
from sqlalchemy import func
from models import db, User, CashMovement, Company, Customer
from forms import MovementForm 
from pdf_reports import pdv_summary_pdf

def _get_company_header():
    try:
        c = Company.query.filter_by(is_default=True).first()
        if not c:
            c = Company.query.order_by(Company.id.asc()).first()
        
        if c:
            return {
                "nome": c.nome_fantasia or c.razao_social or "",
                "endereco": f"{c.logradouro or ''}, {c.numero or ''} - {c.cidade or ''}",
                "cnpj": c.cnpj or ""
            }
    except Exception:
        pass
    return { "nome": "Empresa Não Configurada", "endereco": "", "cnpj": "" }

@pdv_bp.route("/", methods=["GET","POST"])
@login_required
def pdv_index():
    form = MovementForm()
    form.customer_id.choices = [(0, "Nenhum (pagamento à vista)")] + [(c.id, c.nome_razao_social) for c in Customer.query.filter_by(ativo=True).order_by(Customer.nome_razao_social)]
    if form.validate_on_submit():
        tipo, pagamento, customer_id = form.tipo.data, form.pagamento.data, form.customer_id.data if form.customer_id.data != 0 else None
        if pagamento == "CONTA" and tipo != 'VENDA':
            flash("A opção 'Na Conta' só está disponível para 'Venda / Pesagem'.", "danger")
            return render_template("pdv/index.html", form=form)
        if pagamento == "CONTA" and not customer_id:
            flash("Para lançar 'Na Conta', você precisa selecionar um cliente.", "danger")
            return render_template("pdv/index.html", form=form)
        mov = CashMovement(tipo=tipo, valor=Decimal(form.valor.data or 0), pagamento=pagamento, descricao=form.descricao.data, ticket_ref=form.ticket_ref.data, user_id=getattr(current_user, "id", None), customer_id=customer_id, placa=form.placa.data, material=form.material.data, peso=form.peso.data, status="Pendente" if pagamento == "CONTA" else "Pago")
        db.session.add(mov)
        db.session.commit()
        if 'submit' in request.form:
            flash(f"Movimento '{tipo}' lançado! O recibo será impresso.", "success")
            return redirect(url_for('pdv.imprimir_recibo', mov_id=mov.id))
        else:
            flash(f"Movimento '{tipo}' lançado com sucesso!", "success")
            return redirect(url_for("pdv.pdv_index"))
    return render_template("pdv/index.html", form=form)

@pdv_bp.route("/mov")
@login_required
def pdv_list():
    q = request.args.get("q","").strip()
    query = CashMovement.query.order_by(db.desc(CashMovement.created_at))
    if q:
        like = f"%{q}%"
        query = query.filter((CashMovement.descricao.ilike(like)) | (CashMovement.ticket_ref.ilike(like)))
    items = query.limit(200).all()

    # --- LÓGICA DE TOTAIS ATUALIZADA ---
    totals = {
        'DINHEIRO': Decimal('0.0'),
        'PIX': Decimal('0.0'),
        'CARTAO': Decimal('0.0'),
        'SAIDAS': Decimal('0.0')
    }

    for i in items:
        valor = i.valor or Decimal('0.0')
        if (i.tipo == 'VENDA' or i.tipo == 'PAGAMENTO') and i.pagamento in totals:
            totals[i.pagamento] += valor
        elif i.tipo in ['SANGRIA', 'RETIRADA']:
            totals['SAIDAS'] += valor
    
    saldo_dinheiro = totals['DINHEIRO'] - totals['SAIDAS']

    return render_template("pdv/mov_list.html", items=items, totals=totals, saldo_dinheiro=saldo_dinheiro, q=q)

@pdv_bp.route("/recibo/<int:mov_id>")
@login_required
def imprimir_recibo(mov_id):
    mov = CashMovement.query.get_or_404(mov_id)
    empresa = _get_company_header()
    return render_template("pdv/recibo.html", mov=mov, empresa=empresa)

@pdv_bp.route("/test-print")
@login_required
def test_print():
    empresa = _get_company_header()
    mov_teste = {"tipo": "TESTE", "valor": 12.34, "pagamento": "DINHEIRO", "descricao": "Teste de impressão", "created_at": datetime.now()}
    return render_template("pdv/recibo.html", mov=mov_teste, empresa=empresa, is_test=True)

@pdv_bp.route("/mov/relatorio_diario")
@login_required
def relatorio_diario():
    start_date_str = request.args.get('data_inicio')
    end_date_str = request.args.get('data_fim')
    if not start_date_str or not end_date_str:
        flash("Por favor, selecione a data de início e a data de fim.", "danger")
        return redirect(url_for('pdv.pdv_list'))
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Formato de data inválido.", "danger")
        return redirect(url_for('pdv.pdv_list'))
    start_of_day = datetime.combine(start_date, datetime.min.time())
    end_of_day = datetime.combine(end_date, datetime.max.time())
    movements = CashMovement.query.filter(CashMovement.created_at >= start_of_day, CashMovement.created_at <= end_of_day).order_by(CashMovement.created_at.asc()).all()
    if not movements:
        flash(f"Nenhuma movimentação encontrada para o período de {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}.", "info")
        return redirect(url_for('pdv.pdv_list'))
    buffer = io.BytesIO()
    pdv_summary_pdf(buffer, None, movements, start_date, end_date)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'relatorio_caixa_{start_date.strftime("%Y-%m-%d")}_a_{end_date.strftime("%Y-%m-%d")}.pdf', mimetype='application/pdf')