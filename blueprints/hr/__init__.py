from flask import Blueprint
hr_bp = Blueprint('hr', __name__)
from . import routes