# blueprints/billing/routes.py
"""
Rotas de Faturamento/Assinatura
Cliente visualiza plano, valor, vencimento e status
"""

from flask import render_template, g
from flask_login import login_required
from . import billing_bp

@billing_bp.route('/assinatura')
@login_required
def subscription_info():
    """Página de informações da assinatura do tenant"""
    
    # Tenant atual
    tenant = g.tenant
    
    if not tenant:
        return "Tenant não identificado", 404
    
    # Informações da assinatura
    subscription = tenant.subscription
    
    # Calcula dias restantes do trial
    trial_days_remaining = 0
    if tenant.is_trial:
        trial_days_remaining = tenant.trial_days_remaining
    
    # Status do pagamento
    payment_status = 'unknown'
    if tenant.is_trial:
        payment_status = 'trial'
    elif subscription:
        payment_status = subscription.status
    
    # Uso de recursos
    usage = tenant.get_current_usage()
    
    # Histórico de pagamentos
    from models_saas import Payment
    payments = Payment.query.filter_by(tenant_id=tenant.id).order_by(Payment.due_date.desc()).all()
    
    # Separa pagamentos por status
    paid_payments = [p for p in payments if p.status == 'paid']
    pending_payments = [p for p in payments if p.status == 'pending' and not p.is_overdue]
    overdue_payments = [p for p in payments if p.is_overdue]
    
    return render_template('billing/subscription.html',
                         tenant=tenant,
                         subscription=subscription,
                         trial_days_remaining=trial_days_remaining,
                         payment_status=payment_status,
                         usage=usage,
                         payments=payments,
                         paid_payments=paid_payments,
                         pending_payments=pending_payments,
                         overdue_payments=overdue_payments)
