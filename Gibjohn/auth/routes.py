# auth/routes.py — blueprint only (no Flask() here)
from datetime import datetime, timezone
from flask import request, render_template, redirect, url_for, flash, session, make_response
from flask_login import login_user, current_user, login_required, logout_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from email_validator import validate_email, EmailNotValidError

from . import bp  #  Blueprint created in auth/__init__.py;  its name is "auth"
from .forms import RegisterForm, LoginForm, ProfileForm, ChangePasswordForm, DeleteAccountForm
from models import db, User

# If you use Flask-Limiter v3+, you usually init this in app factory and call limiter.limit on routes.Limiter(get_remote_address, default_limits=["200 per day"])
limiter = Limiter(get_remote_address, default_limits=["200 per day"])


# ───────── Register ─────────
@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("learner.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        full_name = " ".join(form.full_name.data.strip().split())
        raw_email = form.email.data.strip()
        pw        = form.password.data
        dob       = form.dob.data      # if your form field is named dob
        role      = form.role.data

        # Normalize + validate email
        try:
            email = validate_email(raw_email, allow_smtputf8=True).normalized
        except EmailNotValidError:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("auth.register"))

        # Unique email
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Try logging in.", "warn")
            return redirect(url_for("auth.login"))

        # Create user (match model fields exactly)
        user = User(
            email=email,        # ✔ matches model
            full_name=full_name, # ✔ matches model
            dob=dob,            # ✔ matches model
            role=role           # ✔ matches model
        )
        user.set_password(pw)

        db.session.add(user)
        try:
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))
        except IntegrityError as err:
            db.session.rollback()
            msg = str(getattr(err, "orig", err))
            print("IntegrityError:", msg)
            if ("UNIQUE" in msg and "email" in msg.lower()):
                flash("That email is already registered.", "warn")
                return redirect(url_for("auth.login"))
            flash(f"DB error: {msg}", "error")
            return redirect(url_for("auth.register"))
        except Exception as err:
            db.session.rollback()
            print("Unexpected DB error:", err)
            flash("Unexpected error creating account.", "error")
            return redirect(url_for("auth.register"))

    if form.errors:
        print("REGISTER ERRORS:", form.errors)
    return render_template("auth/register.html", form=form)


# ───────── Login ─────────
@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("learner_dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        pw = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(pw):
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember.data)
        flash("Welcome back!", "success")

        # Prefer timezone-aware now
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        next_url = request.args.get("next")
        if user.role == "tutor":
            return redirect(next_url or url_for("tutor.tutor_dashboard"))
        if user.role == "learner":
            return redirect(next_url or url_for("learner.dashboard"))
    return render_template("auth/login.html", form=form)

# ───────── Profile (/account) ─────────
@bp.route("/account", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    delete_form = DeleteAccountForm()

    # Delete account branch
    if request.method == "POST" and "delete_submit" in request.form and delete_form.validate_on_submit():
        if not current_user.check_password(delete_form.password.data):
            flash("Password is incorrect.", "error")
            return redirect(url_for("auth.profile"))

        if not delete_form.confirm.data:
            flash("Please confirm deletion before proceeding.", "error")
            return redirect(url_for("auth.profile"))

        try:
            db.session.delete(current_user)
            db.session.commit()
            logout_user()
            flash("Your account has been deleted.", "success")
            return redirect(url_for("home"))
        except Exception as err:
            db.session.rollback()
            print("Unexpected DB error during delete:", err)
            flash("Could not delete account. Please try again.", "error")
            return redirect(url_for("auth.profile"))

    # Update profile branch
    if request.method == "POST" and "submit" in request.form and form.validate_on_submit():
        full_name = " ".join(form.full_name.data.strip().split())
        raw_email = form.email.data.strip()

        try:
            email = validate_email(raw_email, allow_smtputf8=True).normalized
        except EmailNotValidError:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("auth.profile"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            flash("Email already registered to another account.", "error")
            return redirect(url_for("auth.profile"))

        current_user.full_name = full_name
        current_user.email = email
        try:
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("auth.profile"))
        except IntegrityError as err:
            db.session.rollback()
            msg = str(getattr(err, "orig", err))
            print("IntegrityError:", msg)
            if ("UNIQUE" in msg and "email" in msg.lower()) or "uq_users_email" in msg:
                flash("That email is already registered.", "warn")
                return redirect(url_for("auth.profile"))
            flash(f"DB error: {msg}", "error")
            return redirect(url_for("auth.profile"))
        except Exception as err:
            db.session.rollback()
            print("Unexpected DB error:", err)
            flash("Unexpected error updating profile.", "error")
            return redirect(url_for("auth.profile"))

    if form.errors:
        print("PROFILE ERRORS:", form.errors)
    return render_template("profile.html", form=form, delete_form=delete_form)

# ───────── Change password ─────────
@bp.route("/account/password", methods=["GET","POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("auth.change_password"))
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password updated.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/change_password.html", form=form)

# ───────── Logout ─────────
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out.", "success")
    resp = make_response(redirect(url_for("home")))
    resp.delete_cookie("remember_token")
    return resp
