# tutor/__init__.py
from flask import Blueprint
bp = Blueprint('tutor', __name__, template_folder="../templates/tutor")
from . import routes  # noqa 