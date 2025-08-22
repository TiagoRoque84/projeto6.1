# blueprints/customers/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Customer, CashMovement
from forms import CustomerForm
from sqlalchemy import or_

# A criação do Blueprint
customers_bp = Blueprint('customers', __name__)

@customers_bp.route("/")
@login_required
def list():
    q = request.args.get("q", "").strip()
    query = Customer.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Customer.nome_razao_social.ilike(like)) |
            (Customer.cpf_cnpj.ilike(like))
        )
    items = query.order_by(Customer.nome_razao_social).all()
    return render_template("customers/list.html", items=items, q=q)

@customers_bp.route("/novo", methods=["GET", "POST"])
@login_required
def new():
    form = CustomerForm()
    if form.validate_on_submit():
        new_customer = Customer()
        form.populate_obj(new_customer)
        # --- MELHORIA APLICADA AQUI ---
        # Garante que o campo vazio seja salvo como nulo
        if not new_customer.cpf_cnpj:
            new_customer.cpf_cnpj = None
        db.session.add(new_customer)
        db.session.commit()
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for("customers.list"))
    return render_template("customers/form.html", form=form, title="Novo Cliente")

@customers_bp.route("/<int:customer_id>/editar", methods=["GET", "POST"])
@login_required
def edit(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        form.populate_obj(customer)
        # --- MELHORIA APLICADA AQUI ---
        # Garante que o campo vazio seja salvo como nulo
        if not customer.cpf_cnpj:
            customer.cpf_cnpj = None
        db.session.commit()
        flash("Cliente atualizado com sucesso!", "success")
        return redirect(url_for("customers.list"))
    return render_template("customers/form.html", form=form, title="Editar Cliente")

# --- NOVA ROTA PARA O EXTRATO DO CLIENTE ---
@customers_bp.route("/<int:customer_id>/extrato", methods=["GET", "POST"])
@login_required
def account(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Busca todas as pendências (tipo VENDA e status Pendente)
    pending_movements = CashMovement.query.filter_by(
        customer_id=customer.id, 
        tipo='VENDA', 
        status='Pendente'
    ).order_by(CashMovement.created_at.asc()).all()

    # Busca os últimos pagamentos e vendas já pagas para o histórico
    paid_movements = CashMovement.query.filter(
        CashMovement.customer_id==customer.id,
        or_(CashMovement.status=='Pago', CashMovement.tipo=='PAGAMENTO')
    ).order_by(CashMovement.created_at.desc()).limit(20).all()

    total_due = sum(item.valor for item in pending_movements)

    return render_template(
        "customers/account.html", 
        customer=customer, 
        pending_movements=pending_movements,
        paid_movements=paid_movements,
        total_due=total_due
    )

# --- NOVA ROTA PARA PROCESSAR O PAGAMENTO ---
@customers_bp.route("/<int:customer_id>/pagar", methods=["POST"])
@login_required
def pay(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Pega os IDs das pesagens que o usuário marcou para pagar
    movement_ids_to_pay = request.form.getlist('movement_ids', type=int)
    payment_method = request.form.get('payment_method')
    
    if not movement_ids_to_pay:
        flash("Nenhuma pesagem foi selecionada para pagamento.", "warning")
        return redirect(url_for('customers.account', customer_id=customer_id))

    if not payment_method:
        flash("Por favor, selecione a forma de pagamento.", "danger")
        return redirect(url_for('customers.account', customer_id=customer_id))

    # Filtra apenas os movimentos que realmente pertencem ao cliente e estão pendentes
    movements_to_pay = CashMovement.query.filter(
        CashMovement.id.in_(movement_ids_to_pay),
        CashMovement.customer_id == customer_id,
        CashMovement.status == 'Pendente'
    ).all()

    if not movements_to_pay:
        flash("Nenhuma pendência válida encontrada para os itens selecionados.", "error")
        return redirect(url_for('customers.account', customer_id=customer_id))

    total_paid = sum(mov.valor for mov in movements_to_pay)

    # 1. Cria um único registro de PAGAMENTO
    new_payment = CashMovement(
        tipo='PAGAMENTO',
        valor=total_paid,
        pagamento=payment_method,
        descricao=f"Pagamento de {len(movements_to_pay)} pesagem(ns)",
        customer_id=customer_id,
        user_id=getattr(current_user, "id", None),
        status='Pago' # Pagamentos já entram como "Pago"
    )
    db.session.add(new_payment)
    db.session.commit() # Salva para obter o ID do pagamento

    # 2. Atualiza o status das pesagens pagas e as vincula ao novo registro de pagamento
    for mov in movements_to_pay:
        mov.status = 'Pago'
        mov.pagamento_id = new_payment.id # Vincula a dívida ao pagamento

    db.session.commit()

    flash(f"Pagamento de R$ {total_paid:.2f} registrado com sucesso!", "success")
    return redirect(url_for('customers.account', customer_id=customer_id))