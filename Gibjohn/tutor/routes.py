# tutor/routes.py
from datetime import datetime, timezone
import mimetypes
import os

from flask import (
    render_template, request, redirect, url_for, flash,
    current_app, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import db, Resources, Class, Assignment
from . import bp  # blueprint
from flask_wtf import FlaskForm
from tutor.forms import ResourceForm

# --- tiny CSRF-only form for small POST actions (e.g., create/delete buttons)
class EmptyForm(FlaskForm):
    pass


# ---------- Tutor Dashboard ----------
@bp.route("/tutor/dashboard")
@login_required
def tutor_dashboard():
    # If your template has any quick actions (POST buttons), pass a CSRF form
    return render_template("tutor_dashboard.html", form=EmptyForm())


# ---------- Assignments ----------
@bp.route("/assignments", methods=["GET"])
@login_required
def assignments():
    # IMPORTANT: created_at must be a real db.Column, no trailing comma in model
    items = Assignment.query.order_by(Assignment.created_at.desc()).all()
    classes = Class.query.all()
    resources = Resources.query.all()
    return render_template(
        "tutor/assignments.html",
        assignments=items,
        classes=classes,
        resources=resources,
        form=EmptyForm(),  # for inline create/delete forms
    )


@bp.route("/assignments/new", methods=["POST"])
@login_required
def assignments_create():
    # enforce CSRF
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid or expired form. Please try again.", "error")
        return redirect(url_for("tutor.assignments"))

    title = (request.form.get("title") or "").strip()
    class_id = request.form.get("class_id", type=int)
    resource_id = request.form.get("resource_id", type=int)
    due_iso = request.form.get("due_date")  # optional datetime-local string

    if not title or not class_id or not resource_id:
        flash("Please fill title, class and resource.", "error")
        return redirect(url_for("tutor.assignments"))

    a = Assignment(title=title, class_id=class_id, resource_id=resource_id)
    # Optional: parse ISO datetime if provided
    if due_iso:
        try:
            a.due_date = datetime.fromisoformat(due_iso)
        except ValueError:
            flash("Could not parse due date. Please use a valid date/time.", "warn")

    db.session.add(a)
    db.session.commit()
    flash("Assignment created.", "success")
    return redirect(url_for("tutor.assignments"))


@bp.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@login_required
def assignments_delete(assignment_id):
    # enforce CSRF
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid or expired form. Please try again.", "error")
        return redirect(url_for("tutor.assignments"))

    a = db.session.get(Assignment, assignment_id)
    if not a:
        flash("Assignment not found.", "error")
        return redirect(url_for("tutor.assignments"))

    db.session.delete(a)
    db.session.commit()
    flash("Assignment deleted.", "success")
    return redirect(url_for("tutor.assignments"))


# ---------- Classes ----------
@bp.route("/classes/new", methods=["GET", "POST"])
@login_required
def new_class():
    if request.method == "POST":
        # enforce CSRF
        form = EmptyForm()
        if not form.validate_on_submit():
            flash("Invalid or expired form. Please try again.", "error")
            return redirect(url_for("tutor.new_class"))

        title = (request.form.get("title") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        year_group = request.form.get("year_group", type=int)

        if not title or not subject or not year_group:
            flash("Please fill all fields.", "error")
            return redirect(url_for("tutor.new_class"))

        db.session.add(
            Class(
                title=title,
                subject=subject,
                year_group=year_group,
                tutor_id=current_user.user_id,
            )
        )
        db.session.commit()
        flash("Class created.", "success")
        return redirect(url_for("tutor.assignments"))

    # GET
    return render_template("tutor/new_class.html", form=EmptyForm())


# ---------- Resources (files + links) ----------
ALLOWED_EXT = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".m4v",
    ".mp3", ".wav", ".txt", ".csv"
}

def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT


@bp.route("/resources", methods=["GET", "POST"])
@login_required
def resources():
    form = ResourceForm()

    if form.validate_on_submit():
        title = (form.title.data or "").strip()
        description = (form.description.data or "").strip()
        link = (form.link.data or "").strip()
        files = request.files.getlist("files")

        if not title and not files and not link:
            flash("Please provide a title and at least one file or a link.", "error")
            return redirect(url_for("tutor.resources"))

        # 1) Save link as a resource (if provided)
        if link:
            db.session.add(
                Resources(
                    title=title or link,
                    subject="misc",
                    type="link",
                    description=description,
                    url=link,
                    owner_id=current_user.user_id,
                    created_at=datetime.now(timezone.utc),
                )
            )

        # 2) Save files (multiple)
        if files:
            upload_dir = os.path.join(current_app.root_path, "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            for f in files:
                if not f or not f.filename:
                    continue
                filename = secure_filename(f.filename)
                if not allowed_file(filename):
                    flash(f"Skipped {filename}: file type not allowed.", "warn")
                    continue

                # De-dupe filenames
                base, ext = os.path.splitext(filename)
                save_path = os.path.join(upload_dir, filename)
                if os.path.exists(save_path):
                    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
                    filename = f"{base}-{stamp}{ext}"
                    save_path = os.path.join(upload_dir, filename)

                f.save(save_path)

                # Optional: set metadata IF your model has these columns
                kwargs = {}
                if hasattr(Resources, "path"):
                    kwargs["path"] = save_path
                if hasattr(Resources, "mime"):
                    kwargs["mime"] = mimetypes.guess_type(filename)[0] or "application/octet-stream"
                if hasattr(Resources, "size"):
                    try:
                        kwargs["size"] = os.path.getsize(save_path)
                    except OSError:
                        kwargs["size"] = None

                db.session.add(
                    Resources(
                        title=title or filename,
                        subject="misc",
                        type="file",
                        description=description,
                        url=None,
                        owner_id=current_user.user_id,
                        created_at=datetime.now(timezone.utc),
                        **kwargs,
                    )
                )

        db.session.commit()
        flash("Resource(s) saved.", "success")
        return redirect(url_for("tutor.resources"))

    elif request.method == "POST":
        # Form posted but failed validation (e.g., CSRF)
        for field, errs in form.errors.items():
            for e in errs:
                flash(f"{field}: {e}", "error")
        return redirect(url_for("tutor.resources"))

    # GET: list current user's resources
    items = (
        Resources.query.filter_by(owner_id=current_user.user_id)
        .order_by(Resources.created_at.desc())
        .all()
    )
    return render_template("tutor/resources.html", form=form, resources=items)


# ---------- Serve uploaded files (preview/download) ----------
@bp.route("/uploads/<path:filename>")
@login_required
def uploads(filename):
    upload_dir = os.path.join(current_app.root_path, "uploads")
    return send_from_directory(upload_dir, filename, as_attachment=False)
