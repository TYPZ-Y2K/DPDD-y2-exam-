import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY","devsecret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL","sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"   # "Strict" if you don’t embed
    SESSION_COOKIE_SECURE = False     # True in HTTPS/prod
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 60*60*24*30  # 30 days (or timedelta)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # e.g., 50MB

    

    

