# blueprints/fleet/__init__.py
from flask import Blueprint

fleet_bp = Blueprint('fleet', __name__, template_folder='../../templates/fleet')

from . import routes