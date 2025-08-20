# app.py

from flask import Flask
from extensions import db, login_manager, migrate
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.companies import companies_bp
from blueprints.hr import hr_bp
from blueprints.documents import documents_bp
from blueprints.admin import admin_bp
from blueprints.pdv import pdv_bp
from blueprints.uploads import uploads_bp
from blueprints.dash import dash_bp
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def create_app():
    """
    Função factory para criar e configurar a instância da aplicação Flask.
    """
    app = Flask(__name__)
    
    # Configurações da aplicação a partir de variáveis de ambiente
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['UPLOAD_FOLDER'] = 'uploads'

    # Inicializa as extensões com a aplicação
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Registra os blueprints (módulos da aplicação)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(companies_bp, url_prefix='/companies')
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(pdv_bp, url_prefix='/pdv')
    app.register_blueprint(uploads_bp, url_prefix='/uploads')
    app.register_blueprint(dash_bp, url_prefix='/dash')

    print("Home ('/') apontada para dash.dashboard.")
    
    return app
