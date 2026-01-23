# blueprints/super_admin/auth.py
"""
Autenticação do Super Admin
"""

from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models_saas import SuperAdmin
from . import super_admin_auth_bp
from extensions import db

@super_admin_auth_bp.route('/super-admin/login', methods=['GET', 'POST'])
def login():
    """Login do super admin"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        super_admin = SuperAdmin.query.filter_by(username=username).first()
        
        if super_admin and check_password_hash(super_admin.password, password):
            if not super_admin.is_active:
                flash('Conta desativada.', 'error')
                return redirect(url_for('super_admin_auth.login'))
            
            login_user(super_admin, remember=True)
            
            # Atualiza último login
            from datetime import datetime
            import pytz
            super_admin.last_login = datetime.now(pytz.timezone('America/Sao_Paulo'))
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/super-admin'):
                return redirect(next_page)
            return redirect(url_for('super_admin.dashboard'))
        else:
            flash('Credenciais inválidas.', 'error')
    
    return render_template('super_admin/login.html')

@super_admin_auth_bp.route('/super-admin/logout')
@login_required
def logout():
    """Logout do super admin"""
    logout_user()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('super_admin_auth.login'))
