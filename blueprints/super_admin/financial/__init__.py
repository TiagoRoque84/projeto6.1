# blprints/super_admin/financial/__init__.py
"""
Blueprint Financeiro do Super Admin
"""

from flask import Blueprint

financial_bp = Blueprint('financial', __name__)

from . import categories, accounts, transactions, dashboard
