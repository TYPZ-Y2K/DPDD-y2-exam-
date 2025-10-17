# app.py
from flask import Flask, render_template, redirect, url_for, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from config import Config


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day"])

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # security headers (CSP example)
    csp = {
        "default-src": ["'self'"],
        "img-src": ["'self'", "data:"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "script-src": ["'self'"],
    }
    Talisman(app, content_security_policy=csp, force_https=False)  # set True in prod

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # user loader
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"

    # register blueprints
    from auth import bp as auth_bp
    from learner import bp as learner_bp
    from tutor import bp as tutor_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(learner_bp)
    app.register_blueprint(tutor_bp)

    # home route
    @app.route("/")
    def home():
            return render_template("home.html")

    @app.route("/consent")
    def consent():
        resp = make_response(redirect(url_for("home")))
        resp.set_cookie("consent", "yes",
        max_age=60*60*24*365,
        httponly=True, samesite="Lax")
        return resp


    @app.route("/revoke-consent")
    def revoke_consent():
        resp = make_response(redirect(url_for("home")))
        resp.delete_cookie("consent")
        return resp
    return app






if __name__ == "__main__":
    create_app().run(debug=True)
