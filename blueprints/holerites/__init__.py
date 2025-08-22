from flask import Blueprint

holerites_bp = Blueprint('holerites', __name__, template_folder='../../templates/holerites')

from . import routes