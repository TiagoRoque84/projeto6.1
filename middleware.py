# middleware.py
"""
Middleware para identificação automática de tenant e filtragem de queries
"""

from flask import g, request, abort, redirect, url_for
from models_saas import Tenant
from functools import wraps
import re

def get_tenant_from_request():
    """
    Identifica o tenant baseado no subdomínio ou parâmetro de URL
    Retorna None se for o super admin ou tenant não encontrado
    """
    from config import Config
    
    # Se estiver usando subdomínios
    if Config.USE_SUBDOMAINS:
        host = request.host.lower()
        
        # Remove porta se existir
        host = host.split(':')[0]
        
        # Extrai o subdomínio
        # Exemplo: cliente1.local -> cliente1
        #          admin.local -> admin
        parts = host.split('.')
        
        if len(parts) >= 2:
            subdomain = parts[0]
            
            # Se for o subdomínio do super admin, retorna None
            if subdomain == Config.SUPER_ADMIN_SUBDOMAIN:
                return None
            
            # Busca o tenant pelo subdomínio
            tenant = Tenant.query.filter_by(subdomain=subdomain).first()
            return tenant
        
        return None
    
    # Se não estiver usando subdomínios, tenta obter do parâmetro ou sessão
    else:
        # Tenta parâmetro de URL primeiro
        tenant_id = request.args.get('tenant')
        if tenant_id:
            try:
                tenant = Tenant.query.get(int(tenant_id))
                return tenant
            except (ValueError, TypeError):
                return None
        
        # Tenta da sessão
        from flask import session
        tenant_id = session.get('tenant_id')
        if tenant_id:
            tenant = Tenant.query.get(tenant_id)
            return tenant
        
        return None


def init_tenant_context():
    """
    Inicializa o contexto do tenant para a requisição atual
    Deve ser chamado antes de cada requisição
    """
    g.tenant = get_tenant_from_request()
    g.is_super_admin = (g.tenant is None and is_super_admin_request())


def is_super_admin_request():
    """
    Verifica se a requisição é para o painel do super admin
    """
    from config import Config
    
    if Config.USE_SUBDOMAINS:
        host = request.host.lower().split(':')[0]
        parts = host.split('.')
        if len(parts) >= 2:
            return parts[0] == Config.SUPER_ADMIN_SUBDOMAIN
    
    # Verifica se a URL começa com /super-admin/
    return request.path.startswith('/super-admin')


def requires_tenant(f):
    """
    Decorator que exige que haja um tenant válido na requisição
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant') or g.tenant is None:
            abort(404, "Tenant não encontrado")
        
        # Verifica se o tenant está ativo
        if not g.tenant.is_active:
            return "Conta suspensa. Entre em contato com o suporte.", 403
        
        # Verifica se o trial expirou
        if g.tenant.is_trial and g.tenant.is_trial_expired:
            if g.tenant.subscription and g.tenant.subscription.status != 'active':
                return redirect(url_for('billing.trial_expired'))
        
        return f(*args, **kwargs)
    return decorated_function


def requires_super_admin(f):
    """
    Decorator que exige que o usuário seja um super admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from models_saas import SuperAdmin
        
        # Verifica se está logado e é um SuperAdmin
        if not current_user.is_authenticated:
            return redirect(url_for('super_admin_auth.login'))
        
        # Verifica se o user_id começa com "super_" (identificador de SuperAdmin)
        if not str(current_user.get_id()).startswith('super_'):
            abort(403, "Acesso negado")
        
        return f(*args, **kwargs)
    return decorated_function


class TenantQueryFilter:
    """
    Filtro automático de queries por tenant
    """
    
    @staticmethod
    def filter_query(model_class, query):
        """
        Filtra a query automaticamente por tenant_id
        """
        # Verifica se o modelo tem o campo tenant_id
        if hasattr(model_class, 'tenant_id'):
            # Se há um tenant no contexto, filtra por ele
            if hasattr(g, 'tenant') and g.tenant is not None:
                return query.filter(model_class.tenant_id == g.tenant.id)
        
        return query
    
    @staticmethod
    def add_tenant_id(instance):
        """
        Adiciona automaticamente o tenant_id ao criar um novo registro
        """
        if hasattr(instance, 'tenant_id') and hasattr(g, 'tenant'):
            if g.tenant is not None and instance.tenant_id is None:
                instance.tenant_id = g.tenant.id


def validate_tenant_limits(operation_type):
    """
    Decorator para validar limites do tenant antes de operações
    
    operation_type: 'company', 'user', 'employee'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant') or g.tenant is None:
                return f(*args, **kwargs)
            
            from models import Company, User, Employee
            
            # Verifica limites antes de criar
            if operation_type == 'company':
                current_count = Company.query.filter_by(tenant_id=g.tenant.id).count()
                if current_count >= g.tenant.max_companies:
                    abort(403, f"Limite de empresas atingido ({g.tenant.max_companies}). Faça upgrade do seu plano.")
            
            elif operation_type == 'user':
                current_count = User.query.filter_by(tenant_id=g.tenant.id).count()
                if current_count >= g.tenant.max_users:
                    abort(403, f"Limite de usuários atingido ({g.tenant.max_users}). Faça upgrade do seu plano.")
            
            elif operation_type == 'employee':
                if g.tenant.max_employees == 0:
                    abort(403, "Módulo de RH não disponível no seu plano. Faça upgrade.")
                current_count = Employee.query.filter_by(tenant_id=g.tenant.id).count()
                if current_count >= g.tenant.max_employees:
                    abort(403, f"Limite de funcionários atingido ({g.tenant.max_employees}). Faça upgrade do seu plano.")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
