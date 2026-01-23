"""
Blueprint de Billing (Faturamento/Assinatura)
Permite que o cliente visualize informações da sua assinatura
"""
from flask import Blueprint

billing_bp = Blueprint('billing', __name__)

from . import routes
