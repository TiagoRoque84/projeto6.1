from flask import Blueprint
dash_bp = Blueprint('dash', __name__)
from . import routes