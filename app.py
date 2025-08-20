# app.py

import os
from flask import Flask
from extensions import db, login_manager, migrate
from models import User, Company, Funcao, DocumentType
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def create_app():
    """
    Função factory para criar e configurar a instância da aplicação Flask.
    """
    app = Flask(__name__)
    
    # Configurações da aplicação
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializa as extensões com a aplicação
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Importa e registra os blueprints (módulos da aplicação)
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
    
    print("Home ('/') apontada para dash.dashboard.")
    
    return app

# Carrega o usuário para o Flask-Login
@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

# Cria a instância da aplicação
app = create_app()

# Define o comando 'init-data' para o CLI do Flask
@app.cli.command("init-data")
def init_data():
    """Cria os dados iniciais no banco de dados."""
    if not User.query.filter_by(username="admin").first():
        from werkzeug.security import generate_password_hash
        u = User(username="admin", password=generate_password_hash("admin123", method='pbkdf2:sha256'), role="admin", nome_completo="Administrador")
        db.session.add(u)
    if Funcao.query.count() == 0:
        db.session.add(Funcao(nome="Motorista"))
        db.session.add(Funcao(nome="Auxiliar"))
    if DocumentType.query.count() == 0:
        db.session.add(DocumentType(nome="Alvará"))
        db.session.add(DocumentType(nome="Certidão"))
    if Company.query.count() == 0:
        db.session.add(Company(razao_social="Empresa Exemplo LTDA", nome_fantasia="Exemplo", cnpj="00.000.000/0001-00", cidade="São José do Rio Pardo", uf="SP"))
    db.session.commit()
    print("Dados iniciais criados. Login: admin / admin123")


# Executa a aplicação
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)