# blueprints/pdv/routes.py

import os
from decimal import Decimal
from flask import request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import pdv_bp
from datetime import datetime
from sqlalchemy import desc
from models import db, User, CashMovement, Company, Customer
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange, Optional

class MovementForm(FlaskForm):
    tipo = SelectField("Tipo de Movimento", choices=[
        ('VENDA', 'Venda / Pesagem'),
        ('SANGRIA', 'Sangria (Retirada para o cofre)'),
        ('RETIRADA', 'Retirada (Pagamento de despesa)')
    ], validators=[DataRequired()])
    customer_id = SelectField("Cliente (para lançar na conta)", coerce=int, validators=[Optional()])
    valor = DecimalField("Valor (R$)", places=2, validators=[DataRequired(), NumberRange(min=0)])
    ticket_ref = StringField("Ticket de Pesagem")
    placa = StringField("Placa do Veículo")
    material = StringField("Material Pesado")
    peso = FloatField("Peso (kg)", validators=[Optional()])
    pagamento = SelectField("Forma de pagamento", choices=[
        ("DINHEIRO","Dinheiro"),
        ("PIX","Pix"),
        ("CARTAO","Cartão"),
        ("CONTA", "Na Conta (Fiado)")
    ], validators=[DataRequired()])
    descricao = StringField("Descrição/Motivo", validators=[DataRequired()])
    submit = SubmitField("Lançar e imprimir")
    submit_no_print = SubmitField("Apenas lançar")

from utils_printer import print_ticket, build_ticket_lines

def _company_header():
    # ... (código existente, sem alterações)
    try:
        c = Company.query.order_by(Company.id.asc()).first()
        if c:
            header = [ c.nome_fantasia or (c.razao_social or ""), (c.logradouro or "") + (" - " + c.cidade if getattr(c, "cidade", None) else ""), ]
            if getattr(c, "cnpj", None): header.append(f"CNPJ: {c.cnpj}")
            return [h for h in header if h.strip()]
    except Exception: pass
    h1, h2, h3 = os.getenv("TICKET_HEADER_1", "TRANSer"), os.getenv("TICKET_HEADER_2", ""), os.getenv("TICKET_HEADER_3", "")
    return [x for x in [h1,h2,h3] if x]

@pdv_bp.route("/", methods=["GET","POST"])
@login_required
def pdv_index():
    form = MovementForm()
    form.customer_id.choices = [(0, "Nenhum (pagamento à vista)")] + \
                              [(c.id, c.nome_razao_social) for c in Customer.query.filter_by(ativo=True).order_by(Customer.nome_razao_social)]

    if form.validate_on_submit():
        tipo = form.tipo.data
        pagamento = form.pagamento.data
        customer_id = form.customer_id.data if form.customer_id.data != 0 else None

        if pagamento == "CONTA" and tipo != 'VENDA':
            flash("A opção 'Na Conta' só está disponível para 'Venda / Pesagem'.", "danger")
            return render_template("pdv/index.html", form=form)
        if pagamento == "CONTA" and not customer_id:
            flash("Para lançar 'Na Conta', você precisa selecionar um cliente.", "danger")
            return render_template("pdv/index.html", form=form)

        mov = CashMovement(
            tipo=tipo,
            valor=Decimal(form.valor.data or 0),
            pagamento=pagamento,
            descricao=form.descricao.data,
            ticket_ref=form.ticket_ref.data,
            user_id=getattr(current_user, "id", None),
            customer_id=customer_id,
            placa=form.placa.data,
            material=form.material.data,
            peso=form.peso.data,
            status="Pendente" if pagamento == "CONTA" else "Pago"
        )
        db.session.add(mov)
        db.session.commit()

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
        query = query.filter(
            (CashMovement.descricao.ilike(like)) |
            (CashMovement.ticket_ref.ilike(like))
        )
    items = query.limit(200).all()

    # --- LÓGICA DE CÁLCULO DO SALDO CORRIGIDA ---
    total = 0
    for i in items:
        valor = float(i.valor or 0)
        # SOMA SE...
        if (i.tipo == 'VENDA' and i.pagamento != 'CONTA') or \
           (i.tipo == 'PAGAMENTO' and i.pagamento != 'BAIXA'):
            total += valor
        # SUBTRAI SE...
        elif i.tipo in ['SANGRIA', 'RETIRADA']:
            total -= valor
        # IGNORA vendas a prazo ou baixas externas

    return render_template("pdv/mov_list.html", items=items, total=total, q=q)

# ... (a rota test_print continua igual)
@pdv_bp.route("/test-print")
@login_required
def test_print():
    cols = int(os.getenv("TICKET_COLS","40"))
    header = _company_header()
    lines = build_ticket_lines( title="TESTE DE IMPRESSÃO", header_lines=header, cols=cols, fields=[("Modelo","EPSON TM-T20 (ESC/POS)"), ("Colunas", str(cols)), ("OK","Sucesso")] )
    ok, err = print_ticket(lines)
    flash("Impresso!" if ok else f"Falhou: {err}", "success" if ok else "danger")
    return redirect(url_for("pdv.pdv_index"))