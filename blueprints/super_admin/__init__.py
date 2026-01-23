# blueprints/super_admin/__init__.py
"""
Super Admin Blueprint
"""

from flask import Blueprint

super_admin_bp = Blueprint('super_admin', __name__, template_folder='../../templates')
super_admin_auth_bp = Blueprint('super_admin_auth', __name__, template_folder='../../templates')

from . import routes, auth, payments, admins
from .financial import categories, accounts, transactions, dashboard
