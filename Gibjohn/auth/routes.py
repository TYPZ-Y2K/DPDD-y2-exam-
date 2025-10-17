# auth/routes.py  — blueprint only (no Flask() here)
from datetime import datetime, timezone, timedelta
from flask import request, render_template, redirect, url_for, flash, session, make_response
from flask_login import login_user, current_user, login_required, logout_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, OperationalError
from email_validator import validate_email, EmailNotValidError
from . import bp  # <-- use the blueprint
from .forms import RegisterForm, LoginForm, ProfileForm, ChangePasswordForm, DeleteAccountForm, normalize_name
from models import db, User

# Home for this blueprint (optional)
# --- Routes ---
@bp.route("/")
def index():
    return render_template("index.html")

# --- Rate limiting ---
limiter = Limiter(get_remote_address, bp=bp, default_limits=["200 per day"])



@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():

        # 1) Normalise inputs
        student_name = " ".join(form.student_name.data.strip().split())
        raw_email = form.email.data.strip()

        # 2) Validate + normalise email (STRICT)
        try:
            email = validate_email(raw_email, allow_smtputf8=True).normalized
        except EmailNotValidError:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))

        pw = form.password.data

        # 3) Check if email already registered
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Try logging in.", "warn")
            return redirect(url_for("login"))

        # 4) Create + commit (DB-level guarantee)
        user = User(email=email, student_name=student_name)
        user.set_password(pw)
        db.session.add(user)

        try:   # commit
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

        except IntegrityError as err: # e.g. UNIQUE constraint
            db.session.rollback()
            msg = str(getattr(err, "orig", err))
            print("IntegrityError:", msg)
            if ("UNIQUE" in msg and "email" in msg.lower()) or "uq_users_email" in msg:
                flash("That email is already registered.", "warn")
                return redirect(url_for("login"))
            else:
                flash(f"DB error: {msg}", "error")
                return redirect(url_for("register"))

        except Exception as err: # catch-all
            db.session.rollback()
            print("Unexpected DB error:", err)
            flash("Unexpected error creating account.", "error")
            return redirect(url_for("register"))

    # If we get here, either GET or validation failed → show errors
    if form.errors:
        print("REGISTER ERRORS:", form.errors)  # dev-only
    return render_template("register.html", form=form) 

@limiter.limit("20 per hour")   # e.g., 20 login attempts/hour per IP
@bp.route("/login", methods=["GET", "POST"])  
def login():
    if current_user.is_authenticated: #
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        pw = form.password.data 
        user = User.query.filter_by(email=email).first() 
        if not user or not user.check_password(pw):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember.data)
        flash("Welcome back!", "success")
        from datetime import datetime
    # after successful login, update last_login
        user.last_login = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("login.html", form=form)


@bp.route("/account", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user) # pre-fill with current data
    delete_form = DeleteAccountForm()

    # Handle delete request first if triggered
    if request.method == "POST" and "delete_submit" in request.form and delete_form.validate_on_submit():
        if not current_user.check_password(delete_form.password.data):
            flash("Password is incorrect.", "error")
            return redirect(url_for("profile"))
        try:
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash("Your account has been deleted.", "success")
            return redirect(url_for("index"))
        except Exception as err: # catch-all
            db.session.rollback()
            print("Unexpected DB error during delete:", err)
            flash("Could not delete account. Please try again.", "error")
            return redirect(url_for("profile"))

    if request.method == "POST" and "submit" in request.form and form.validate_on_submit():
        # 1) Normalise inputs
        student_name = " ".join(form.student_name.data.strip().split())
        raw_email = form.email.data.strip()

        # 2) Validate + normalise email (STRICT)
        try:
            email = validate_email(raw_email, allow_smtputf8=True).normalized
        except EmailNotValidError:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("profile"))

        # 3) Check if email already registered to another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            flash("Email already registered to another account.", "error")
            return redirect(url_for("profile"))

        # 4) Update + commit
        current_user.student_name = student_name
        current_user.email = email
        try:
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))
        except IntegrityError as err: # e.g. UNIQUE constraint
            db.session.rollback()
            msg = str(getattr(err, "orig", err))
            print("IntegrityError:", msg)
            if ("UNIQUE" in msg and "email" in msg.lower()) or "uq_users_email" in msg:
                flash("That email is already registered.", "warn")
                return redirect(url_for("profile"))
            else:
                flash(f"DB error: {msg}", "error")
                return redirect(url_for("profile"))
        except Exception as err: # catch-all
            db.session.rollback()
            print("Unexpected DB error:", err)
            flash("Unexpected error updating profile.", "error")
            return redirect(url_for("profile"))

    # If we get here, either GET or validation failed → show errors
    if form.errors:
        print("PROFILE ERRORS:", form.errors)  # dev-only
    return render_template("profile.html", form=form, delete_form=delete_form)

@bp.route("account/password", methods=["GET","POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("change_password"))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password updated.", "success")
        return redirect(url_for("profile"))
    return render_template("change_password.html", form=form)

@bp.route("/logout")
@login_required
def logout():
    logout_user() # clears Flask-Login session + remember
    session.clear() # belt-and-braces
    flash("Logged out.", "success")
    resp = make_response(redirect(url_for("index"))) # create response
    # in case a stale remember cookie remains under a custom domain/path
    resp.delete_cookie("remember_token")
    return resp
