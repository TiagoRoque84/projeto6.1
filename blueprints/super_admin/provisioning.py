# blueprints/super_admin/provisioning.py
"""
Sistema de provisionamento automático de novos tenants
"""

from extensions import db
from models_saas import Tenant, Subscription, TenantFeature
from models import User
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import pytz
import secrets
import string

def generate_password(length=12):
    """Gera uma senha aleatória segura"""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def provision_new_tenant(data):
    """
    Provisiona um novo tenant automaticamente
    
    Args:
        data (dict): {
            'subdomain': str,
            'company_name': str,
            'contact_name': str,
            'contact_email': str,
            'contact_phone': str (optional),
            'plan_type': str (basic, professional, enterprise),
            'trial_days': int,
            'send_email': bool
        }
    
    Returns:
        dict: {
            'success': bool,
            'tenant': Tenant object,
            'user': User object,
            'password': str (senha gerada),
            'error': str (se houver erro)
        }
    """
    from config import Config
    
    try:
        # 1. Cria o Tenant
        now = datetime.now(pytz.timezone('America/Sao_Paulo'))
        trial_ends = now + timedelta(days=data.get('trial_days', Config.TRIAL_DAYS))
        
        plan_type = data.get('plan_type', 'basic')
        plan_config = Config.PLANS.get(plan_type)
        
        if not plan_config:
            return {'success': False, 'error': 'Plano inválido'}
        
        tenant = Tenant(
            subdomain=data['subdomain'],
            company_name=data['company_name'],
            contact_name=data['contact_name'],
            contact_email=data['contact_email'],
            contact_phone=data.get('contact_phone', ''),
            is_active=True,
            created_at=now,
            activated_at=now,
            trial_ends_at=trial_ends,
            is_trial=True,
            max_companies=plan_config['max_companies'],
            max_users=plan_config['max_users'],
            max_employees=plan_config['max_employees'],
            storage_limit_gb=plan_config['storage_gb']
        )
        
        db.session.add(tenant)
        db.session.flush()  # Para obter o tenant.id
        
        # 2. Cria a Subscription
        subscription = Subscription(
            tenant_id=tenant.id,
            plan_type=plan_type,
            price=plan_config['price'],
            billing_cycle='monthly',
            status='trial',
            current_period_start=now.date(),
            current_period_end=trial_ends.date(),
            next_billing_date=trial_ends.date()
        )
        
        db.session.add(subscription)
        
        # 3. Habilita as features do plano
        for feature_code in plan_config['features']:
            feature = TenantFeature(
                tenant_id=tenant.id,
                feature_code=feature_code,
                is_enabled=True
            )
            db.session.add(feature)
        
        # 4. Cria o usuário admin do tenant
        password = generate_password()
        username = f"admin_{data['subdomain']}"
        
        admin_user = User(
            tenant_id=tenant.id,
            username=username,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            role='admin',
            active=True,
            nome_completo=data['contact_name']
        )
        
        db.session.add(admin_user)
        
        # 5. Commit de tudo
        db.session.commit()
        
        # 6. Envia email de boas-vindas (se solicitado)
        if data.get('send_email', False):
            send_welcome_email(tenant, admin_user, password)
        
        return {
            'success': True,
            'tenant': tenant,
            'user': admin_user,
            'password': password
        }
    
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

def send_welcome_email(tenant, user, password):
    """
    Envia email de boas-vindas com credenciais
    
    TODO: Implementar envio de email quando configurado
    """
    from config import Config
    
    if not Config.MAIL_USERNAME:
        # Email não configurado ainda
        return False
    
    # TODO: Implementar integração com serviço de email
    # Exemplo de conteúdo:
    """
    Olá {tenant.contact_name}!
    
    Seja bem-vindo(a) ao nosso sistema de gestão!
    
    Seu período de trial de {Config.TRIAL_DAYS} dias começou.
    
    Acesse seu painel em: http://{tenant.subdomain}.{Config.BASE_DOMAIN}
    
    Credenciais:
    Usuário: {user.username}
    Senha: {password}
    
    Recomendamos trocar sua senha no primeiro acesso.
    
    Qualquer dúvida, estamos à disposição!
    """
    
    print(f"[EMAIL DEBUG] Enviaria email para {tenant.contact_email}")
    print(f"Subdomain: {tenant.subdomain}")
    print(f"Username: {user.username}")
    print(f"Password: {password}")
    
    return True
