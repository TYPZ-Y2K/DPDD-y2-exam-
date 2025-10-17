import os
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY","devsecret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL","sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class Config:
    SECRET_KEY = "devsecret"  # use env var in prod
    # ...
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"   # "Strict" if you don’t embed
    SESSION_COOKIE_SECURE = False     # True in HTTPS/prod
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 60*60*24*30  # 30 days (or timedelta)

