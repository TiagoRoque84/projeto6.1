# blueprints/super_admin/financial/categories.py
"""
Gerenciamento de Categorias Financeiras
"""

from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
from blueprints.super_admin import super_admin_bp
from middleware import requires_super_admin
from models_financial import FinancialCategory
from extensions import db

@super_admin_bp.route('/super-admin/financial/categories')
@login_required
@requires_super_admin
def financial_categories():
    """Lista de categorias"""
    receitas = FinancialCategory.query.filter_by(type='receita', is_active=True).order_by(FinancialCategory.name).all()
    despesas = FinancialCategory.query.filter_by(type='despesa', is_active=True).order_by(FinancialCategory.name).all()
    
    return render_template('super_admin/financial/categories_list.html',
                         receitas=receitas,
                         despesas=despesas)

@super_admin_bp.route('/super-admin/financial/categories/new', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def financial_category_new():
    """Criar nova categoria"""
    if request.method == 'POST':
        try:
            category = FinancialCategory(
                name=request.form.get('name'),
                type=request.form.get('type'),
                description=request.form.get('description'),
                color=request.form.get('color', '#667eea'),
                icon=request.form.get('icon', '📊'),
                is_active=True
            )
            
            db.session.add(category)
            db.session.commit()
            
            flash(f'Categoria "{category.name}" criada com sucesso!', 'success')
            return redirect(url_for('super_admin.financial_categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar categoria: {str(e)}', 'error')
    
    return render_template('super_admin/financial/category_form.html',
                         category=None,
                         title='Nova Categoria')

@super_admin_bp.route('/super-admin/financial/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def financial_category_edit(category_id):
    """Editar categoria"""
    category = FinancialCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        try:
            category.name = request.form.get('name')
            category.type = request.form.get('type')
            category.description = request.form.get('description')
            category.color = request.form.get('color')
            category.icon = request.form.get('icon')
            
            db.session.commit()
            
            flash(f'Categoria "{category.name}" atualizada!', 'success')
            return redirect(url_for('super_admin.financial_categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'error')
    
    return render_template('super_admin/financial/category_form.html',
                         category=category,
                         title='Editar Categoria')

@super_admin_bp.route('/super-admin/financial/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@requires_super_admin
def financial_category_delete(category_id):
    """Excluir categoria"""
    category = FinancialCategory.query.get_or_404(category_id)
    
    try:
        # Verificar se há lançamentos usando esta categoria
        if category.transactions.count() > 0:
            flash(f'Não é possível excluir "{category.name}" pois existem lançamentos vinculados. Desative ao invés de excluir.', 'error')
        else:
            db.session.delete(category)
            db.session.commit()
            flash(f'Categoria "{category.name}" excluída!', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.financial_categories'))

@super_admin_bp.route('/super-admin/financial/categories/<int:category_id>/toggle', methods=['POST'])
@login_required
@requires_super_admin
def financial_category_toggle(category_id):
    """Ativar/Desativar categoria"""
    category = FinancialCategory.query.get_or_404(category_id)
    
    try:
        category.is_active = not category.is_active
        db.session.commit()
        
        status = "ativada" if category.is_active else "desativada"
        flash(f'Categoria "{category.name}" {status}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.financial_categories'))
