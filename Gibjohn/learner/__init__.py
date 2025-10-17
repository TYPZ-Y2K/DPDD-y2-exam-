# tutor/__init__.py
from flask import Blueprint
bp = Blueprint("learner", __name__, template_folder="../templates")
from . import routes  # noqa