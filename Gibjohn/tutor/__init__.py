# tutor/__init__.py
from flask import Blueprint
bp = Blueprint('tutor', __name__, url_prefix='/tutor', template_folder='templates')
from . import routes  # noqa 