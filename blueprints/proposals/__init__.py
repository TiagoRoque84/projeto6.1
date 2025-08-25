# blueprints/proposals/__init__.py
from flask import Blueprint

proposals_bp = Blueprint('proposals', __name__, template_folder='../../templates')

from . import routes