# app.py

import os
from flask import Flask, g
from extensions import db, login_manager, migrate
from models import User
# Importar modelos SaaS para Flask-Migrate detectar
from models_saas import Tenant, Subscription, TenantFeature, SuperAdmin, TenantInvitation
import models_financial  # Sistema financeiro
from dotenv import load_dotenv
from config import Config

load_dotenv()

def normalize_upload_path(path):
    if not path: return ""
    rel_path = str(path).replace('\\', '/')
    if rel_path.startswith('uploads/'): rel_path = rel_path[len('uploads/'):]
    return rel_path

def create_app():
    app = Flask(__name__, template_folder="templates")
    
    # Configuração
    app.config.from_object(Config)
    
    # Filtros Jinja
    app.jinja_env.filters['norm_upload'] = normalize_upload_path
    
    # Inicializa extensões
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # =============================================
    # MIDDLEWARE MULTI-TENANT
    # =============================================
    from middleware import init_tenant_context
    from decorators import inject_feature_context
    
    @app.before_request
    def before_request():
        """Identifica o tenant antes de cada requisição"""
        init_tenant_context()
    
    @app.context_processor
    def inject_context():
        """Injeta variáveis de contexto nos templates"""
        return inject_feature_context()
    
    # =============================================
    # BLUEPRINTS
    # =============================================
    
    # Super Admin (novo)
    from blueprints.super_admin import super_admin_bp, super_admin_auth_bp
    app.register_blueprint(super_admin_auth_bp)
    app.register_blueprint(super_admin_bp)
    
    # Blueprints existentes
    from blueprints.main.routes import main_bp
    from blueprints.auth.routes import auth_bp
    from blueprints.companies.routes import companies_bp
    from blueprints.hr.routes import hr_bp
    from blueprints.documents.routes import documents_bp
    from blueprints.admin.routes import admin_bp
    from blueprints.admin.users import admin_users_bp
    from blueprints.pdv.routes import pdv_bp
    from blueprints.uploads.routes import uploads_bp
    from blueprints.dash.routes import dash_bp
    from blueprints.customers.routes import customers_bp
    from blueprints.epi import epi_bp
    from blueprints.agendamentos import agendamentos_bp
    from blueprints.holerites import holerites_bp
    from blueprints.proposals import proposals_bp
    from blueprints.billing import billing_bp
    from blueprints.fleet.routes import fleet_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(companies_bp, url_prefix='/empresas')
    app.register_blueprint(hr_bp, url_prefix='/rh')
    app.register_blueprint(documents_bp, url_prefix='/documentos')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(admin_users_bp, url_prefix="/admin/usuarios")
    app.register_blueprint(pdv_bp, url_prefix='/pdv')
    app.register_blueprint(uploads_bp)
    app.register_blueprint(dash_bp, url_prefix='/dash')
    app.register_blueprint(customers_bp, url_prefix='/clientes')
    app.register_blueprint(epi_bp, url_prefix='/epi')
    app.register_blueprint(agendamentos_bp, url_prefix='/agendamentos')
    app.register_blueprint(holerites_bp, url_prefix='/holerites')
    app.register_blueprint(proposals_bp, url_prefix='/orcamentos')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(fleet_bp, url_prefix='/frota')
    
    print("🚀 Sistema SaaS Multi-Tenant inicializado!")
    print(f"   Modo: {'DESENVOLVIMENTO' if Config.DEVELOPMENT_MODE else 'PRODUÇÃO'}")
    print(f"   Domínio base: {Config.BASE_DOMAIN}")
    
    # Handlers de Erro Personalizados
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    return app

@login_manager.user_loader
def load_user(uid):
    """Carrega usuário (pode ser SuperAdmin ou User regular)"""
    # Se o ID começa com "super_", é um SuperAdmin
    if str(uid).startswith('super_'):
        super_id = int(uid.replace('super_', ''))
        return SuperAdmin.query.get(super_id)
    
    # Caso contrário, é um User regular
    return User.query.get(int(uid))

app = create_app()

@app.cli.command("init-data")
def init_data():
    """Inicializa dados básicos do sistema"""
    from werkzeug.security import generate_password_hash
    from models import Funcao, DocumentType, Company
    from config import Config
    
    # Cria super admin se não existir
    if not SuperAdmin.query.filter_by(username=Config.SUPER_ADMIN_USERNAME).first():
        super_admin = SuperAdmin(
            username=Config.SUPER_ADMIN_USERNAME,
            password=generate_password_hash(Config.SUPER_ADMIN_PASSWORD, method='pbkdf2:sha256'),
            email=Config.SUPER_ADMIN_EMAIL,
            nome_completo="Super Administrador",
            is_active=True
        )
        db.session.add(super_admin)
        print(f"✅ Super Admin criado: {Config.SUPER_ADMIN_USERNAME} / {Config.SUPER_ADMIN_PASSWORD}")
    
    # Dados básicos (sem tenant - serão compartilhados ou criados por tenant)
    if Funcao.query.count() == 0:
        db.session.add(Funcao(nome="Motorista"))
        db.session.add(Funcao(nome="Auxiliar"))
        print("✅ Funções criadas")
    
    if DocumentType.query.count() == 0:
        db.session.add(DocumentType(nome="Alvará"))
        db.session.add(DocumentType(nome="Certidão"))
        print("✅ Tipos de documento criados")
    
    db.session.commit()
    print("✅ Dados iniciais criados com sucesso!")

@app.cli.command("create-demo-tenant")
def create_demo_tenant():
    """Cria um tenant de demonstração"""
    from blueprints.super_admin.provisioning import provision_new_tenant
    
    data = {
        'subdomain': 'demo',
        'company_name': 'Empresa Demonstração LTDA',
        'contact_name': 'Admin Demo',
        'contact_email': 'demo@exemplo.com',
        'contact_phone': '(16) 99999-9999',
        'plan_type': 'professional',
        'trial_days': 30,
        'send_email': False
    }
    
    result = provision_new_tenant(data)
    
    if result['success']:
        print(f"✅ Tenant demo criado com sucesso!")
        print(f"   Subdomínio: demo.{Config.BASE_DOMAIN}")
        print(f"   Usuário: {result['user'].username}")
        print(f"   Senha: {result['password']}")
    else:
        print(f"❌ Erro ao criar tenant: {result.get('error')}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=Config.DEVELOPMENT_MODE)