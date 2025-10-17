import os
import sys

# Ensure project root is on sys.path when executed as a script
_CURRENT_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    # When executed as a module: python -m auth.bootstrap
    from app import app  # Flask app instance
except ModuleNotFoundError:
    # When executed directly: python auth/bootstrap.py
    from routes import app  # type: ignore

from models import db, User  # SQLAlchemy db instance
from sqlalchemy import inspect  # for introspecting DB

# --- Create DB tables ---
with app.app_context():
    db.create_all()
    print("Tables:", inspect(db.engine).get_table_names())
    print("DB path:", db.engine.url)
