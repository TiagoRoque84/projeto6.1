"""
Configuração do Sistema SaaS Multi-Tenant
Suporta tanto ambiente de desenvolvimento local quanto produção
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # =============================================
    # MODO DE OPERAÇÃO
    # =============================================
    # True = Desenvolvimento local com subdomínios .local
    # False = Produção com domínio real
    DEVELOPMENT_MODE = os.environ.get('DEVELOPMENT_MODE', 'True').lower() == 'true'
    
    # =============================================
    # MULTI-TENANCY
    # =============================================
    # Se True, usa subdomínios para identificar tenants
    # Se False, usa parâmetro ?tenant=X (útil para debug)
    USE_SUBDOMAINS = os.environ.get('USE_SUBDOMAINS', 'True').lower() == 'true'
    
    # Domínio base
    BASE_DOMAIN = os.environ.get('BASE_DOMAIN', 'local' if DEVELOPMENT_MODE else 'seudominio.com')
    
    # Subdomínio do Super Admin
    SUPER_ADMIN_SUBDOMAIN = os.environ.get('SUPER_ADMIN_SUBDOMAIN', 'admin')
    
    # =============================================
    # FLASK
    # =============================================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # =============================================
    # DATABASE
    # =============================================
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 
        'sqlite:///saas_app.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # =============================================
    # UPLOAD
    # =============================================
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max
    
    # =============================================
    # PLANOS E FEATURES
    # =============================================
    PLANS = {
        'basic': {
            'name': 'Básico',
            'price': 97.00,
            'max_companies': 1,
            'max_users': 3,
            'max_employees': 0,
            'storage_gb': 5,
            'features': ['documents'],
            'description': 'Ideal para pequenas empresas com foco em documentação'
        },
        'professional': {
            'name': 'Profissional',
            'price': 197.00,
            'max_companies': 3,
            'max_users': 10,
            'max_employees': 30,
            'storage_gb': 20,
            'features': ['documents', 'hr', 'scheduling', 'customers'],
            'description': 'Solução completa para empresas em crescimento'
        },
        'enterprise': {
            'name': 'Empresarial',
            'price': 397.00,
            'max_companies': 999,  # "ilimitado"
            'max_users': 999,
            'max_employees': 999,
            'storage_gb': 100,
            'features': ['documents', 'hr', 'scheduling', 'customers', 'epi', 'fleet', 'pdv'],
            'description': 'Todos os recursos para grandes operações'
        }
    }
    
    # Mapeamento de features para nomes amigáveis
    FEATURE_NAMES = {
        'documents': 'Gestão de Documentos',
        'hr': 'Recursos Humanos',
        'scheduling': 'Agendamentos',
        'customers': 'Clientes',
        'epi': 'EPIs',
        'fleet': 'Gestão de Frota',
        'pdv': 'PDV/Caixa'
    }
    
    # =============================================
    # TRIAL
    # =============================================
    TRIAL_DAYS = int(os.environ.get('TRIAL_DAYS', 14))
    
    # =============================================
    # EMAIL (para envio de credenciais)
    # =============================================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@seudominio.com')
    
    # =============================================
    # SUPER ADMIN
    # =============================================
    # Credenciais do super admin (será criado automaticamente)
    SUPER_ADMIN_USERNAME = os.environ.get('SUPER_ADMIN_USERNAME', 'superadmin')
    SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'admin123')
    SUPER_ADMIN_EMAIL = os.environ.get('SUPER_ADMIN_EMAIL', 'admin@seudominio.com')
