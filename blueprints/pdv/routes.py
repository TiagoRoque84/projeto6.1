\
import os
from decimal import Decimal
from flask import request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import pdv_bp

from datetime import datetime
from sqlalchemy import desc

try:
    # Importar modelos do projeto principal
    from models import db, User  # db deve existir em models
except Exception:
    # fallback: pegar de extensions se for o padrão do seu projeto
    from extensions import db

# Modelo simples de movimentos de caixa (caso não exista no models principal)
class CashMovement(db.Model):  # tabela: cash_movement
    __tablename__ = "cash_movement"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # VENDA, SANGRIA, RETIRADA
    valor = db.Column(db.Numeric(10,2), nullable=False)
    pagamento = db.Column(db.String(20), nullable=False)  # DINHEIRO, PIX, CARTAO
    descricao = db.Column(db.String(255))
    ticket_ref = db.Column(db.String(50))  # número do ticket de pesagem (opcional)
    cliente = db.Column(db.String(120))    # nome/identificação do cliente (opcional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

# WTForms locais para não depender do forms.py global
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class MovForm(FlaskForm):
    tipo = SelectField("Tipo de movimento", choices=[
        ("VENDA","Venda"),
        ("SANGRIA","Sangria"),
        ("RETIRADA","Retirada"),
    ], validators=[DataRequired()])
    valor = DecimalField("Valor (R$)", places=2, validators=[DataRequired(), NumberRange(min=0)])
    pagamento = SelectField("Forma de pagamento", choices=[
        ("DINHEIRO","Dinheiro"),
        ("PIX","Pix"),
        ("CARTAO","Cartão"),
    ], validators=[DataRequired()])
    descricao = StringField("Descrição", validators=[Optional()])
    ticket_ref = StringField("Ticket (opcional)", validators=[Optional()])
    cliente = StringField("Cliente (opcional)", validators=[Optional()])
    submit = SubmitField("Lançar e imprimir")
    submit_no_print = SubmitField("Apenas lançar")

# Utilitário de impressão
from utils_printer import print_ticket, build_ticket_lines

def _company_header():
    # Tenta montar um cabeçalho com base no cadastro de empresa (se existir)
    try:
        from models import Company
        c = Company.query.order_by(Company.id.asc()).first()
        if c:
            header = [
                c.nome_fantasia or (c.razao_social or ""),
                (c.endereco or "") + (" - " + c.cidade if getattr(c, "cidade", None) else ""),
            ]
            if getattr(c, "cnpj", None):
                header.append(f"CNPJ: {c.cnpj}")
            return [h for h in header if h.strip()]
    except Exception:
        pass
    # Fallback: variáveis de ambiente
    h1 = os.getenv("TICKET_HEADER_1", "TRANSer")
    h2 = os.getenv("TICKET_HEADER_2", "")
    h3 = os.getenv("TICKET_HEADER_3", "")
    return [x for x in [h1,h2,h3] if x]

@pdv_bp.route("/pdv", methods=["GET","POST"])
@login_required
def pdv_index():
    form = MovForm()
    if form.validate_on_submit():
        mov = CashMovement(
            tipo=form.tipo.data,
            valor=Decimal(form.valor.data or 0),
            pagamento=form.pagamento.data,
            descricao=form.descricao.data or "",
            ticket_ref=form.ticket_ref.data or "",
            cliente=form.cliente.data or "",
            user_id=getattr(current_user, "id", None)
        )
        db.session.add(mov)
        db.session.commit()
        # Imprime?
        if form.submit.data:
            header = _company_header()
            cols = int(os.getenv("TICKET_COLS","40"))
            lines = build_ticket_lines(
                title="COMPROVANTE DE CAIXA",
                header_lines=header,
                cols=cols,
                fields=[
                    ("Tipo", mov.tipo),
                    ("Valor", f"R$ {mov.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X",".")),
                    ("Forma", mov.pagamento),
                    ("Cliente", mov.cliente or "-"),
                    ("Ticket", mov.ticket_ref or "-"),
                    ("Descrição", mov.descricao or "-"),
                    ("Data", mov.created_at.strftime("%d/%m/%Y %H:%M")),
                ],
                ask_signature=(mov.tipo in ("SANGRIA","RETIRADA"))
            )
            ok, err = print_ticket(lines)
            if not ok:
                flash(f"Movimento salvo, mas falha na impressão: {err}", "warning")
            else:
                flash("Movimento lançado e impresso!", "success")
        else:
            flash("Movimento lançado.", "success")
        return redirect(url_for("pdv.pdv_index"))
    return render_template("pdv/index.html", form=form)

@pdv_bp.route("/pdv/mov")
@login_required
def pdv_list():
    q = request.args.get("q","").strip()
    query = CashMovement.query.order_by(db.desc(CashMovement.created_at))
    if q:
        like = f"%{q}%"
        query = query.filter(
            (CashMovement.descricao.ilike(like)) |
            (CashMovement.ticket_ref.ilike(like)) |
            (CashMovement.cliente.ilike(like)) |
            (CashMovement.tipo.ilike(like))
        )
    items = query.limit(200).all()
    total = sum([float(i.valor or 0) if i.tipo=="VENDA" else (-float(i.valor or 0)) for i in items])
    return render_template("pdv/mov_list.html", items=items, total=total, q=q)

@pdv_bp.route("/pdv/test-print")
@login_required
def test_print():
    cols = int(os.getenv("TICKET_COLS","40"))
    header = _company_header()
    lines = build_ticket_lines(
        title="TESTE DE IMPRESSÃO",
        header_lines=header,
        cols=cols,
        fields=[("Modelo","EPSON TM-T20 (ESC/POS)"), ("Colunas", str(cols)), ("OK","Sucesso")]
    )
    ok, err = print_ticket(lines)
    flash("Impresso!" if ok else f"Falhou: {err}", "success" if ok else "danger")
    return redirect(url_for("pdv.pdv_index"))
