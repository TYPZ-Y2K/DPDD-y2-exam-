# tutor/__init__.py
from flask import Blueprint
bp = Blueprint("learner", __name__, template_folder="../templates/learner")
from . import routes  # noqa