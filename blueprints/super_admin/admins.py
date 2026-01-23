# blueprints/super_admin/admins.py
"""
Gerenciamento de Usuários Super Admin
"""

from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
from blueprints.super_admin import super_admin_bp
from middleware import requires_super_admin
from models_saas import SuperAdmin
from extensions import db
from werkzeug.security import generate_password_hash

@super_admin_bp.route('/super-admin/admins')
@login_required
@requires_super_admin
def superadmins_list():
    """Lista de super admins"""
    admins = SuperAdmin.query.order_by(SuperAdmin.created_at.desc()).all()
    return render_template('super_admin/admins_list.html', admins=admins)

@super_admin_bp.route('/super-admin/admins/new', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def superadmin_new():
    """Criar novo super admin"""
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            nome_completo = request.form.get('nome_completo')
            
            # Verificar se username já existe
            if SuperAdmin.query.filter_by(username=username).first():
                flash('Este nome de usuário já está em uso!', 'error')
                return render_template('super_admin/admin_form.html', admin=None, title='Novo Super Admin')
            
            admin = SuperAdmin(
                username=username,
                password=generate_password_hash(password, method='pbkdf2:sha256'),
                email=email,
                nome_completo=nome_completo,
                is_active=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            flash(f'Super Admin "{username}" criado com sucesso!', 'success')
            return redirect(url_for('super_admin.superadmins_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar: {str(e)}', 'error')
    
    return render_template('super_admin/admin_form.html', admin=None, title='Novo Super Admin')

@super_admin_bp.route('/super-admin/admins/<int:admin_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def superadmin_edit(admin_id):
    """Editar super admin"""
    admin = SuperAdmin.query.get_or_404(admin_id)
    
    # Proteger o super admin principal
    if admin.username == 'superadmin':
        flash('O Super Admin principal não pode ser editado por segurança!', 'error')
        return redirect(url_for('super_admin.superadmins_list'))
    
    if request.method == 'POST':
        try:
            # Atualizar dados
            admin.email = request.form.get('email')
            admin.nome_completo = request.form.get('nome_completo')
            
            # Atualizar senha apenas se fornecida
            new_password = request.form.get('password')
            if new_password:
                admin.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            
            db.session.commit()
            
            flash(f'Super Admin "{admin.username}" atualizado!', 'success')
            return redirect(url_for('super_admin.superadmins_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {str(e)}', 'error')
    
    return render_template('super_admin/admin_form.html', admin=admin, title='Editar Super Admin')

@super_admin_bp.route('/super-admin/admins/<int:admin_id>/toggle', methods=['POST'])
@login_required
@requires_super_admin
def superadmin_toggle(admin_id):
    """Ativar/Desativar super admin"""
    admin = SuperAdmin.query.get_or_404(admin_id)
    
    # Proteger o super admin principal
    if admin.username == 'superadmin':
        flash('O Super Admin principal não pode ser desativado!', 'error')
        return redirect(url_for('super_admin.superadmins_list'))
    
    try:
        admin.is_active = not admin.is_active
        db.session.commit()
        
        status = "ativado" if admin.is_active else "desativado"
        flash(f'Super Admin "{admin.username}" {status}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.superadmins_list'))

@super_admin_bp.route('/super-admin/admins/<int:admin_id>/delete', methods=['POST'])
@login_required
@requires_super_admin
def superadmin_delete(admin_id):
    """Excluir super admin"""
    admin = SuperAdmin.query.get_or_404(admin_id)
    
    # Proteger o super admin principal
    if admin.username == 'superadmin':
        flash('O Super Admin principal não pode ser excluído!', 'error')
        return redirect(url_for('super_admin.superadmins_list'))
    
    try:
        db.session.delete(admin)
        db.session.commit()
        flash(f'Super Admin "{admin.username}" excluído!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.superadmins_list'))
