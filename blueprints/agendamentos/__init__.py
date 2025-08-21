# blueprints/agendamentos/__init__.py
from flask import Blueprint

agendamentos_bp = Blueprint('agendamentos', __name__, template_folder='../../templates/agendamentos')

from . import routes