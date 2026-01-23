# blueprints/super_admin/financial/dashboard.py
"""
Dashboard Financeiro
"""

from flask import render_template
from flask_login import login_required
from blueprints.super_admin import super_admin_bp
from middleware import requires_super_admin
from models_financial import FinancialTransaction, BankAccount, FinancialCategory
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func

@super_admin_bp.route('/super-admin/financial/dashboard')
@login_required
@requires_super_admin
def financial_dashboard():
    """Dashboard financeiro completo"""
    
    # Saldo total das contas (soma do current_balance)
    accounts = BankAccount.query.filter_by(is_active=True).all()
    total_balance = sum(float(acc.current_balance or 0) for acc in accounts)
    
    # Receitas e Despesas do mês atual
    today = datetime.now().date()
    first_day = today.replace(day=1)
    
    receitas_mes = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.type == 'receita',
        FinancialTransaction.status == 'paid',
        FinancialTransaction.payment_date >= first_day
    ).scalar() or 0
    
    despesas_mes = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.type == 'despesa',
        FinancialTransaction.status == 'paid',
        FinancialTransaction.payment_date >= first_day
    ).scalar() or 0
    
    # Contas a receber/pagar próximos 30 dias
    next_30_days = today + timedelta(days=30)
    
    a_receber = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.type == 'receita',
        FinancialTransaction.status == 'pending',
        FinancialTransaction.due_date <= next_30_days
    ).scalar() or 0
    
    a_pagar = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.type == 'despesa',
        FinancialTransaction.status == 'pending',
        FinancialTransaction.due_date <= next_30_days
    ).scalar() or 0
    
    # Últimas transações
    recent_transactions = FinancialTransaction.query.order_by(
        FinancialTransaction.created_at.desc()
    ).limit(10).all()
    
    # Contas bancárias
    bank_accounts = BankAccount.query.filter_by(is_active=True).all()
    
    # Receitas por categoria (top 5)
    receitas_by_category = db.session.query(
        FinancialCategory.name,
        FinancialCategory.color,
        FinancialCategory.icon,
        func.sum(FinancialTransaction.amount).label('total')
    ).join(FinancialTransaction).filter(
        FinancialTransaction.type == 'receita',
        FinancialTransaction.status == 'paid',
        FinancialTransaction.payment_date >= first_day
    ).group_by(FinancialCategory.id).order_by(func.sum(FinancialTransaction.amount).desc()).limit(5).all()
    
    # Despesas por categoria (top 5)
    despesas_by_category = db.session.query(
        FinancialCategory.name,
        FinancialCategory.color,
        FinancialCategory.icon,
        func.sum(FinancialTransaction.amount).label('total')
    ).join(FinancialTransaction).filter(
        FinancialTransaction.type == 'despesa',
        FinancialTransaction.status == 'paid',
        FinancialTransaction.payment_date >= first_day
    ).group_by(FinancialCategory.id).order_by(func.sum(FinancialTransaction.amount).desc()).limit(5).all()
    
    return render_template('super_admin/financial/dashboard.html',
                         total_balance=float(total_balance),
                         receitas_mes=float(receitas_mes),
                         despesas_mes=float(despesas_mes),
                         a_receber=float(a_receber),
                         a_pagar=float(a_pagar),
                         saldo_mes=float(receitas_mes) - float(despesas_mes),
                         recent_transactions=recent_transactions,
                         bank_accounts=bank_accounts,
                         receitas_by_category=receitas_by_category,
                         despesas_by_category=despesas_by_category)
