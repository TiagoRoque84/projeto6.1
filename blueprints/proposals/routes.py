# blueprints/proposals/routes.py
from flask import render_template
from flask_login import login_required

# A linha mais importante é esta, que importa a variável do __init__.py
from . import proposals_bp

# Exemplo de uma rota para listar os orçamentos
@proposals_bp.route("/")
@login_required
def list():
    return "<h1>Página de Orçamentos</h1>"