# blueprints/super_admin/payments.py
"""
Rotas para gerenciamento de pagamentos do Super Admin
"""

from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
from . import super_admin_bp
from middleware import requires_super_admin
from models_saas import Tenant, Payment
from extensions import db
from datetime import datetime, date, timedelta
import pytz

@super_admin_bp.route('/tenants/<int:tenant_id>/payments/new', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def create_payment(tenant_id):
    """Criar nova fatura para um tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    if request.method == 'POST':
        try:
            # Dados do formulário
            description = request.form.get('description')
            amount = float(request.form.get('amount'))
            due_date_str = request.form.get('due_date')
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            
            # Gerar número da fatura
            import random
            invoice_number = f"INV-{tenant_id}-{datetime.now().strftime('%Y%m')}-{random.randint(1000, 9999)}"
            
            # Criar pagamento
            payment = Payment(
                tenant_id=tenant_id,
                invoice_number=invoice_number,
                amount=amount,
                description=description,
                due_date=due_date,
                status='pending'
            )
            
            db.session.add(payment)
            db.session.commit()
            
            flash(f'Fatura {invoice_number} criada com sucesso!', 'success')
            return redirect(url_for('super_admin.tenant_detail', tenant_id=tenant_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar fatura: {str(e)}', 'error')
    
    # GET - Sugerir valores padrão
    suggested_amount = tenant.subscription.price if tenant.subscription else 0
    suggested_description = f"Mensalidade {datetime.now().strftime('%B/%Y')}"
    suggested_due_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
    
    return render_template('super_admin/payment_form.html',
                         tenant=tenant,
                         suggested_amount=suggested_amount,
                         suggested_description=suggested_description,
                         suggested_due_date=suggested_due_date)

@super_admin_bp.route('/payments/<int:payment_id>/mark-paid', methods=['POST'])
@login_required
@requires_super_admin
def mark_payment_paid(payment_id):
    """Dar baixa em uma fatura"""
    payment = Payment.query.get_or_404(payment_id)
    
    try:
        payment.status = 'paid'
        payment.paid_at = datetime.now(pytz.timezone('America/Sao_Paulo'))
        payment.payment_method = request.form.get('payment_method', 'manual')
        payment.notes = request.form.get('notes', '')
        
        db.session.commit()
        
        flash(f'Pagamento {payment.invoice_number} confirmado!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao confirmar pagamento: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.tenant_detail', tenant_id=payment.tenant_id))

@super_admin_bp.route('/payments/<int:payment_id>/cancel', methods=['POST'])
@login_required
@requires_super_admin
def cancel_payment(payment_id):
    """Cancelar uma fatura"""
    payment = Payment.query.get_or_404(payment_id)
    
    try:
        payment.status = 'cancelled'
        payment.notes = request.form.get('notes', 'Cancelado pelo administrador')
        
        db.session.commit()
        
        flash(f'Fatura {payment.invoice_number} cancelada!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar fatura: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.tenant_detail', tenant_id=payment.tenant_id))
