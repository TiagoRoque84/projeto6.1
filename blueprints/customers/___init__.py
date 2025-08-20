# blueprints/customers/__init__.py

from flask import Blueprint

customers_bp = Blueprint('customers', __name__, template_folder='../../templates')

from . import routes