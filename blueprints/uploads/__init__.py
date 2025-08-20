from flask import Blueprint
uploads_bp = Blueprint('uploads', __name__)
from . import routes