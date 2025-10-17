# auth/__init__.py
from flask import Blueprint
bp = Blueprint("test", __name__, template_folder="../templates")
from . import routes  # noqa