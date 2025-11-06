# app.py
from flask import Flask, app, flash, render_template, redirect, url_for, request, make_response
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_migrate import Migrate
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from config import Config
from models import db, User
from auth.routes import limiter



login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


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

app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB per request

#--- Routes ---
# debug: dump all routes at startup
@app.before_request
def _dump_routes_once():
    if not getattr(app, "_routes_dumped", False):
        print("\n=== ROUTES (endpoint -> url) ===")
        for r in app.url_map.iter_rules():
            print(f"{r.endpoint:25} -> {r.rule}")
        print("================================\n")
        app._routes_dumped = True



@app.route("/consent")
def consent():
    resp = make_response(redirect(url_for("home")))
    resp.set_cookie("consent", "yes",
    max_age=60*60*24*365,
    httponly=True, samesite="Lax")
    flash("Thank you for accepting cookies.", "success")
    return resp
def revoke_consent():
    resp = make_response(redirect(url_for("home")))
    resp.delete_cookie("consent", "no")
    return resp

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/coming_soon")
def coming_soon():
    return render_template("coming_soon.html")

#--- Error handlers ---
@app.errorhandler(CSRFError) # CSRF errors
def handle_csrf_error(e):
    # surfaces: missing, invalid, expired, wrong referer, etc.
    flash(f"Form security check failed: {e.description}", "error")
    return redirect(request.referrer or url_for("home")), 400
@app.errorhandler(429) # too many requests
def ratelimit_handler(e):
    return render_template("429.html", error=e), 429


if __name__ == "__main__":
    app.run(debug=True)
