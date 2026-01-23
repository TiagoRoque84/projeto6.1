# blueprints/super_admin/financial/transactions.py
"""
Gerenciamento de Lançamentos Financeiros
"""

from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from blueprints.super_admin import super_admin_bp
from middleware import requires_super_admin
from models_financial import FinancialTransaction, FinancialCategory, BankAccount, PaymentMethod
from extensions import db
from decimal import Decimal
from datetime import datetime, date

@super_admin_bp.route('/super-admin/financial/transactions')
@login_required
@requires_super_admin
def financial_transactions():
    """Lista de lançamentos financeiros"""
    # Filtros
    type_filter = request.args.get('type', 'all')  # all, receita, despesa
    status_filter = request.args.get('status', 'all')  # all, pending, paid
    
    query = FinancialTransaction.query
    
    # Aplicar filtros
    if type_filter != 'all':
        query = query.filter_by(type=type_filter)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    transactions = query.order_by(FinancialTransaction.due_date.desc()).limit(100).all()
    
    # Estatísticas
    receitas_pendentes = db.session.query(db.func.sum(FinancialTransaction.amount)).filter_by(
        type='receita', status='pending'
    ).scalar() or 0
    
    despesas_pendentes = db.session.query(db.func.sum(FinancialTransaction.amount)).filter_by(
        type='despesa', status='pending'
    ).scalar() or 0
    
    receitas_pagas = db.session.query(db.func.sum(FinancialTransaction.amount)).filter_by(
        type='receita', status='paid'
    ).scalar() or 0
    
    despesas_pagas = db.session.query(db.func.sum(FinancialTransaction.amount)).filter_by(
        type='despesa', status='paid'
    ).scalar() or 0
    
    return render_template('super_admin/financial/transactions_list.html',
                         transactions=transactions,
                         type_filter=type_filter,
                         status_filter=status_filter,
                         receitas_pendentes=float(receitas_pendentes),
                         despesas_pendentes=float(despesas_pendentes),
                         receitas_pagas=float(receitas_pagas),
                         despesas_pagas=float(despesas_pagas))

@super_admin_bp.route('/super-admin/financial/transactions/new', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def financial_transaction_new():
    """Criar novo lançamento"""
    if request.method == 'POST':
        try:
            transaction_type = request.form.get('type')
            amount = Decimal(request.form.get('amount'))
            due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
            
            transaction = FinancialTransaction(
                type=transaction_type,
                category_id=request.form.get('category_id') or None,
                description=request.form.get('description'),
                amount=amount,
                due_date=due_date,
                status='pending',
                payment_method_id=request.form.get('payment_method_id') or None,
                bank_account_id=request.form.get('bank_account_id') or None,
                notes=request.form.get('notes'),
                created_by=current_user.id
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'Lançamento de {transaction_type} criado com sucesso!', 'success')
            return redirect(url_for('super_admin.financial_transactions'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar lançamento: {str(e)}', 'error')
    
    # Carregar dados para o formulário
    categories = FinancialCategory.query.filter_by(is_active=True).order_by(FinancialCategory.name).all()
    accounts = BankAccount.query.filter_by(is_active=True).order_by(BankAccount.name).all()
    payment_methods = PaymentMethod.query.filter_by(is_active=True).order_by(PaymentMethod.name).all()
    
    return render_template('super_admin/financial/transaction_form.html',
                         transaction=None,
                         title='Novo Lançamento',
                         categories=categories,
                         accounts=accounts,
                         payment_methods=payment_methods)

@super_admin_bp.route('/super-admin/financial/transactions/<int:transaction_id>/pay', methods=['POST'])
@login_required
@requires_super_admin
def financial_transaction_pay(transaction_id):
    """Dar baixa em um lançamento"""
    transaction = FinancialTransaction.query.get_or_404(transaction_id)
    
    try:
        # Marcar como pago
        transaction.status = 'paid'
        transaction.payment_date = date.today()
        
        # Atualizar saldo da conta bancária se informada
        if transaction.bank_account_id:
            account = BankAccount.query.get(transaction.bank_account_id)
            if account:
                if transaction.type == 'receita':
                    account.current_balance += transaction.amount
                else:  # despesa
                    account.current_balance -= transaction.amount
        
        db.session.commit()
        flash(f'Baixa registrada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao dar baixa: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.financial_transactions'))

@super_admin_bp.route('/super-admin/financial/transactions/<int:transaction_id>/delete', methods=['POST'])
@login_required
@requires_super_admin
def financial_transaction_delete(transaction_id):
    """Excluir lançamento"""
    transaction = FinancialTransaction.query.get_or_404(transaction_id)
    
    try:
        # Se já foi pago, reverter o saldo da conta
        if transaction.status == 'paid' and transaction.bank_account_id:
            account = BankAccount.query.get(transaction.bank_account_id)
            if account:
                if transaction.type == 'receita':
                    account.current_balance -= transaction.amount
                else:
                    account.current_balance += transaction.amount
        
        db.session.delete(transaction)
        db.session.commit()
        flash('Lançamento excluído!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.financial_transactions'))
