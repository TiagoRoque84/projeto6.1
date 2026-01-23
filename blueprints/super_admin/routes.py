# blueprints/super_admin/routes.py
"""
Rotas do Super Admin Dashboard
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models_saas import Tenant, Subscription, TenantFeature, SuperAdmin
from models import User, Company
from . import super_admin_bp
from middleware import requires_super_admin
from extensions import db
from .provisioning import provision_new_tenant
import json

@super_admin_bp.route('/super-admin/')
@login_required
@requires_super_admin
def dashboard():
    """Dashboard principal do super admin"""
    # Estatísticas
    total_tenants = Tenant.query.count()
    active_tenants = Tenant.query.filter_by(is_active=True).count()
    trial_tenants = Tenant.query.filter_by(is_trial=True, is_active=True).count()
    
    # Receita mensal estimada (somente tenants ativos e não em trial)
    active_subscriptions = Subscription.query.join(Tenant).filter(
        Subscription.status == 'active',
        Tenant.is_trial == False,
        Tenant.is_active == True
    ).all()
    
    monthly_revenue = sum(float(sub.price or 0) for sub in active_subscriptions)
    
    # Tenants recentes
    recent_tenants = Tenant.query.order_by(Tenant.created_at.desc()).limit(10).all()
    
    # Trials expirando em breve (próximos 3 dias)
    from datetime import datetime, timedelta
    import pytz
    now = datetime.now(pytz.timezone('America/Sao_Paulo'))
    three_days = now + timedelta(days=3)
    
    expiring_trials = Tenant.query.filter(
        Tenant.is_trial == True,
        Tenant.trial_ends_at <= three_days,
        Tenant.trial_ends_at > now,
        Tenant.is_active == True
    ).all()
    
    return render_template('super_admin/dashboard.html',
                         total_tenants=total_tenants,
                         active_tenants=active_tenants,
                         trial_tenants=trial_tenants,
                         monthly_revenue=monthly_revenue,
                         recent_tenants=recent_tenants,
                         expiring_trials=expiring_trials)

@super_admin_bp.route('/super-admin/tenants')
@login_required
@requires_super_admin
def tenants_list():
    """Lista todos os tenants"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtros
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = Tenant.query
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True, is_trial=False)
    elif status_filter == 'trial':
        query = query.filter_by(is_trial=True, is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    if search:
        query = query.filter(
            db.or_(
                Tenant.company_name.ilike(f'%{search}%'),
                Tenant.subdomain.ilike(f'%{search}%'),
                Tenant.contact_email.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(Tenant.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('super_admin/tenants_list.html',
                         tenants=pagination.items,
                         pagination=pagination,
                         status_filter=status_filter,
                         search=search)

@super_admin_bp.route('/super-admin/tenants/new', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def tenant_new():
    """Criar novo tenant"""
    from config import Config
    
    if request.method == 'POST':
        try:
            # Dados do formulário
            data = {
                'subdomain': request.form.get('subdomain').lower().strip(),
                'company_name': request.form.get('company_name').strip(),
                'contact_name': request.form.get('contact_name').strip(),
                'contact_email': request.form.get('contact_email').lower().strip(),
                'contact_phone': request.form.get('contact_phone', '').strip(),
                'plan_type': request.form.get('plan_type', 'basic'),
                'trial_days': int(request.form.get('trial_days', Config.TRIAL_DAYS)),
                'send_email': request.form.get('send_email') == 'on'
            }
            
            # Validações
            if Tenant.query.filter_by(subdomain=data['subdomain']).first():
                flash(f"Subdomínio '{data['subdomain']}' já está em uso.", 'error')
                return render_template('super_admin/tenant_new.html', plans=Config.PLANS, data=data)
            
            if Tenant.query.filter_by(contact_email=data['contact_email']).first():
                flash(f"E-mail '{data['contact_email']}' já está cadastrado.", 'error')
                return render_template('super_admin/tenant_new.html', plans=Config.PLANS, data=data)
            
            # Provisiona o novo tenant
            result = provision_new_tenant(data)
            
            if result['success']:
                flash(f"Tenant '{data['subdomain']}' criado com sucesso!", 'success')
                if result.get('password'):
                    flash(f"Senha gerada: {result['password']} (anote antes de sair desta página)", 'info')
                return redirect(url_for('super_admin.tenant_detail', tenant_id=result['tenant'].id))
            else:
                flash(f"Erro ao criar tenant: {result.get('error', 'Erro desconhecido')}", 'error')
                return render_template('super_admin/tenant_new.html', plans=Config.PLANS, data=data)
        
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar tenant: {str(e)}", 'error')
            return render_template('super_admin/tenant_new.html', plans=Config.PLANS)
    
    return render_template('super_admin/tenant_new.html', plans=Config.PLANS)

@super_admin_bp.route('/super-admin/tenants/<int:tenant_id>')
@login_required
@requires_super_admin
def tenant_detail(tenant_id):
    """Detalhes de um tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # Estatísticas de uso
    usage = tenant.get_current_usage()
    
    # Verifica limites
    within_limits, limit_message = tenant.is_within_limits()
    
    # Usuários do tenant
    users = User.query.filter_by(tenant_id=tenant_id).all()
    
    # Empresas do tenant
    companies = Company.query.filter_by(tenant_id=tenant_id).all()
    
    # Pagamentos do tenant
    from models_saas import Payment
    payments = Payment.query.filter_by(tenant_id=tenant_id).order_by(Payment.due_date.desc()).all()
    
    return render_template('super_admin/tenant_detail.html',
                         tenant=tenant,
                         usage=usage,
                         within_limits=within_limits,
                         limit_message=limit_message,
                         users=users,
                         companies=companies,
                         payments=payments)

@super_admin_bp.route('/super-admin/tenants/<int:tenant_id>/toggle-status', methods=['POST'])
@login_required
@requires_super_admin
def tenant_toggle_status(tenant_id):
    """Ativa/desativa um tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    tenant.is_active = not tenant.is_active
    
    from datetime import datetime
    import pytz
    if not tenant.is_active:
        tenant.deactivated_at = datetime.now(pytz.timezone('America/Sao_Paulo'))
    else:
        tenant.deactivated_at = None
    
    db.session.commit()
    
    status = 'ativado' if tenant.is_active else 'desativado'
    flash(f"Tenant '{tenant.subdomain}' {status} com sucesso!", 'success')
    
    return redirect(url_for('super_admin.tenant_detail', tenant_id=tenant_id))

@super_admin_bp.route('/super-admin/tenants/<int:tenant_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_super_admin
def tenant_edit(tenant_id):
    """Editar tenant"""
    from config import Config
    tenant = Tenant.query.get_or_404(tenant_id)
    
    if request.method == 'POST':
        try:
            # Atualiza informações básicas
            tenant.company_name = request.form.get('company_name').strip()
            tenant.contact_name = request.form.get('contact_name').strip()
            tenant.contact_email = request.form.get('contact_email').lower().strip()
            tenant.contact_phone = request.form.get('contact_phone', '').strip()
            
            # Atualiza plano se mudou
            new_plan = request.form.get('plan_type')
            if tenant.subscription and tenant.subscription.plan_type != new_plan:
                plan_config = Config.PLANS.get(new_plan)
                if plan_config:
                    tenant.subscription.plan_type = new_plan
                    tenant.subscription.price = plan_config['price']
                    
                    # Atualiza limites
                    tenant.max_companies = plan_config['max_companies']
                    tenant.max_users = plan_config['max_users']
                    tenant.max_employees = plan_config['max_employees']
                    tenant.storage_limit_gb = plan_config['storage_gb']
                    
                    # Atualiza features
                    TenantFeature.query.filter_by(tenant_id=tenant.id).delete()
                    for feature_code in plan_config['features']:
                        feature = TenantFeature(tenant_id=tenant.id, feature_code=feature_code)
                        db.session.add(feature)
            
            db.session.commit()
            flash('Tenant atualizado com sucesso!', 'success')
            return redirect(url_for('super_admin.tenant_detail', tenant_id=tenant_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tenant: {str(e)}', 'error')
    
    return render_template('super_admin/tenant_edit.html', tenant=tenant, plans=Config.PLANS)

@super_admin_bp.route('/super-admin/tenants/<int:tenant_id>/extend-trial', methods=['POST'])
@login_required
@requires_super_admin
def tenant_extend_trial(tenant_id):
    """Adiciona dias ao trial do tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    try:
        days = int(request.form.get('days', 0))
        if days <= 0:
            flash('Número de dias inválido.', 'error')
            return redirect(url_for('super_admin.tenant_detail', tenant_id=tenant_id))
        
        from datetime import timedelta
        import pytz
        
        if tenant.trial_ends_at:
            # Se trial_ends_at é naive, tornar aware
            if tenant.trial_ends_at.tzinfo is None:
                tenant.trial_ends_at = pytz.timezone('America/Sao_Paulo').localize(tenant.trial_ends_at)
            tenant.trial_ends_at = tenant.trial_ends_at + timedelta(days=days)
        else:
            from datetime import datetime
            now = datetime.now(pytz.timezone('America/Sao_Paulo'))
            tenant.trial_ends_at = now + timedelta(days=days)
            tenant.is_trial = True
        
        db.session.commit()
        flash(f'Trial estendido por {days} dias!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao estender trial: {str(e)}', 'error')
    
    return redirect(url_for('super_admin.tenant_detail', tenant_id=tenant_id))

@super_admin_bp.route('/super-admin/tenants/<int:tenant_id>/cancel-trial', methods=['POST'])
@login_required
@requires_super_admin
def tenant_cancel_trial(tenant_id):
    """Cancela o trial e desativa o tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    tenant.is_trial = False
    tenant.is_active = False
    
    if tenant.subscription:
        tenant.subscription.status = 'cancelled'
    
    from datetime import datetime
    import pytz
    tenant.deactivated_at = datetime.now(pytz.timezone('America/Sao_Paulo'))
    
    db.session.commit()
    flash(f'Trial cancelado e tenant desativado.', 'success')
    
    return redirect(url_for('super_admin.tenant_detail', tenant_id=tenant_id))

@super_admin_bp.route('/super-admin/tenants/<int:tenant_id>/convert-to-paid', methods=['POST'])
@login_required
@requires_super_admin
def tenant_convert_to_paid(tenant_id):
    """Converte trial para plano pago"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    tenant.is_trial = False
    
    if tenant.subscription:
        tenant.subscription.status = 'active'
        from datetime import datetime, timedelta
        now = datetime.now().date()
        tenant.subscription.current_period_start = now
        tenant.subscription.current_period_end = now + timedelta(days=30)
        tenant.subscription.next_billing_date = now + timedelta(days=30)
    
    db.session.commit()
    flash('Tenant convertido para plano pago!', 'success')
    
    return redirect(url_for('super_admin.tenant_detail', tenant_id=tenant_id))

@super_admin_bp.route('/super-admin/tenants/<int:tenant_id>/update-alert-email', methods=['POST'])
@login_required
@requires_super_admin
def tenant_update_alert_email(tenant_id):
    """Atualiza e-mail de alertas do tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    tenant.alert_email = request.form.get('alert_email', '').strip()
    
    db.session.commit()
    flash('E-mail de alertas atualizado!', 'success')
    
    return redirect(url_for('super_admin.tenant_detail', tenant_id=tenant_id))
