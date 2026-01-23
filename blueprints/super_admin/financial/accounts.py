# blueprints/super_admin/financial/accounts.py
"""
Gerenciamento de Contas Bancárias
"""

from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
from blueprints.super_admin import super_admin_bp
from middleware import requires_super_admin
from models_financial import BankAccount
from extensions import db
from decimal import Decimal

@super_admin_bp.route('/super-admin/financial/accounts')
@login_required
@requires_super_admin
def financial_accounts():
    """Lista de contas bancárias"""
    accounts = BankAccount.query.filter_by(is_active=True).order_by(BankAccount.name).all()
    
    # Calcular saldo total
    total_balance = sum(float(acc.current_balance) for acc in accounts)
    
    return render_template('super_admin/financial/accounts_list.html',
                         accounts=accounts,
                         total_balance=total_balance)

@super_admin_bp.route('/super-admin/financial/accounts/new', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def financial_account_new():
    """Criar nova conta bancária"""
    if request.method == 'POST':
        try:
            initial_balance = Decimal(request.form.get('initial_balance', 0))
            
            account = BankAccount(
                name=request.form.get('name'),
                bank_name=request.form.get('bank_name'),
                agency=request.form.get('agency'),
                account_number=request.form.get('account_number'),
                account_type=request.form.get('account_type', 'corrente'),
                initial_balance=initial_balance,
                current_balance=initial_balance,  # Saldo atual = saldo inicial
                is_active=True
            )
            
            db.session.add(account)
            db.session.commit()
            
            flash(f'Conta "{account.name}" criada com sucesso!', 'success')
            return redirect(url_for('super_admin.financial_accounts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar conta: {str(e)}', 'error')
    
    return render_template('super_admin/financial/account_form.html',
                         account=None,
                         title='Nova Conta Bancária')

@super_admin_bp.route('/super-admin/financial/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def financial_account_edit(account_id):
    """Editar conta bancária"""
    account = BankAccount.query.get_or_404(account_id)
    
    if request.method == 'POST':
        try:
            account.name = request.form.get('name')
            account.bank_name = request.form.get('bank_name')
            account.agency = request.form.get('agency')
            account.account_number = request.form.get('account_number')
            account.account_type = request.form.get('account_type')
            
            # Não permitir alterar saldo inicial aqui para não bagunçar a contabilidade
            # Saldo deve ser alterado apenas por transações
            
            db.session.commit()
            
            flash(f'Conta "{account.name}" atualizada!', 'success')
            return redirect(url_for('super_admin.financial_accounts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'error')
    
    return render_template('super_admin/financial/account_form.html',
                         account=account,
                         title='Editar Conta Bancária')

@super_admin_bp.route('/super-admin/financial/accounts/<int:account_id>/toggle', methods=['POST'])
@login_required
@requires_super_admin
def financial_account_toggle(account_id):
    """Ativar/Desativar conta"""
    account = BankAccount.query.get_or_404(account_id)
    
    try:
        account.is_active = not account.is_active
        db.session.commit()
        
        status = "ativada" if account.is_active else "desativada"
        flash(f'Conta "{account.name}" {status}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.financial_accounts'))

@super_admin_bp.route('/super-admin/financial/accounts/<int:account_id>/delete', methods=['POST'])
@login_required
@requires_super_admin
def financial_account_delete(account_id):
    """Excluir conta"""
    account = BankAccount.query.get_or_404(account_id)
    
    try:
        # Verificar se há transações
        if account.transactions.count() > 0:
            flash(f'Não é possível excluir "{account.name}" pois existem transações vinculadas. Desative ao invés de excluir.', 'error')
        else:
            db.session.delete(account)
            db.session.commit()
            flash(f'Conta "{account.name}" excluída!', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.financial_accounts'))
