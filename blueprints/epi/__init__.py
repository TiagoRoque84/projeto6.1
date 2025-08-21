# blueprints/epi/__init__.py
from flask import Blueprint

# Define o blueprint para o módulo de EPI
epi_bp = Blueprint('epi', __name__, template_folder='../../templates/epi')

# Importa as rotas para que sejam associadas ao blueprint
from . import routes