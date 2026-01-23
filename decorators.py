# decorators.py
"""
Decorators para controle de acesso a features/módulos por plano
"""

from functools import wraps
from flask import g, abort, redirect, url_for, flash, render_template
from flask_login import current_user

def requires_feature(feature_code):
    """
    Decorator que verifica se o tenant tem acesso a uma feature específica
    
    Usage:
        @requires_feature('hr')
        def employee_list():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Se não há tenant (super admin), permite acesso
            if not hasattr(g, 'tenant') or g.tenant is None:
                return f(*args, **kwargs)
            
            # Verifica se o tenant tem a feature
            if not g.tenant.has_feature(feature_code):
                from config import Config
                feature_name = Config.FEATURE_NAMES.get(feature_code, feature_code)
                
                # Renderiza página de upgrade
                return render_template(
                    'errors/feature_not_available.html',
                    feature_name=feature_name,
                    feature_code=feature_code,
                    current_plan=g.tenant.subscription.plan_type if g.tenant.subscription else 'basic'
                ), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requires_any_feature(*feature_codes):
    """
    Decorator que verifica se o tenant tem acesso a PELO MENOS UMA das features
    
    Usage:
        @requires_any_feature('hr', 'scheduling')
        def dashboard():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Se não há tenant (super admin), permite acesso
            if not hasattr(g, 'tenant') or g.tenant is None:
                return f(*args, **kwargs)
            
            # Verifica se o tenant tem pelo menos uma das features
            has_access = any(g.tenant.has_feature(code) for code in feature_codes)
            
            if not has_access:
                from config import Config
                feature_names = [Config.FEATURE_NAMES.get(code, code) for code in feature_codes]
                
                return render_template(
                    'errors/feature_not_available.html',
                    feature_name=' ou '.join(feature_names),
                    feature_code=feature_codes[0],
                    current_plan=g.tenant.subscription.plan_type if g.tenant.subscription else 'basic'
                ), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requires_all_features(*feature_codes):
    """
    Decorator que verifica se o tenant tem acesso a TODAS as features
    
    Usage:
        @requires_all_features('hr', 'scheduling')
        def advanced_dashboard():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Se não há tenant (super admin), permite acesso
            if not hasattr(g, 'tenant') or g.tenant is None:
                return f(*args, **kwargs)
            
            # Verifica se o tenant tem todas as features
            missing_features = [
                code for code in feature_codes 
                if not g.tenant.has_feature(code)
            ]
            
            if missing_features:
                from config import Config
                feature_names = [Config.FEATURE_NAMES.get(code, code) for code in missing_features]
                
                return render_template(
                    'errors/feature_not_available.html',
                    feature_name=', '.join(feature_names),
                    feature_code=missing_features[0],
                    current_plan=g.tenant.subscription.plan_type if g.tenant.subscription else 'basic'
                ), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_feature_access(feature_code):
    """
    Função auxiliar para verificar acesso a uma feature programaticamente
    Retorna True/False
    
    Usage:
        if check_feature_access('hr'):
            # mostrar menu de RH
    """
    if not hasattr(g, 'tenant') or g.tenant is None:
        return True  # Super admin tem acesso a tudo
    
    return g.tenant.has_feature(feature_code)


def get_available_features():
    """
    Retorna lista de features disponíveis para o tenant atual
    
    Usage:
        features = get_available_features()
        # ['documents', 'hr', 'scheduling']
    """
    if not hasattr(g, 'tenant') or g.tenant is None:
        from config import Config
        return list(Config.FEATURE_NAMES.keys())  # Super admin tem todas
    
    from models_saas import TenantFeature
    features = TenantFeature.query.filter_by(
        tenant_id=g.tenant.id,
        is_enabled=True
    ).all()
    
    return [f.feature_code for f in features]


def inject_feature_context():
    """
    Context processor para injetar informações de features nos templates
    """
    return {
        'check_feature': check_feature_access,
        'available_features': get_available_features(),
        'current_tenant': g.tenant if hasattr(g, 'tenant') else None
    }
