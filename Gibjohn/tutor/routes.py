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
from models import db, Resources, Class, Assignment, ClassEnrollment, Submission, User, ActivityLog
from sqlalchemy import func, desc
from . import bp  # blueprint
from flask_wtf import FlaskForm
from tutor.forms import ResourceForm, ClassForm, AssignmentForm, AddStudentSearchForm, AddStudentConfirmForm

# --- tiny CSRF-only form for small POST actions (e.g., create/delete buttons)
class EmptyForm(FlaskForm):
    pass


# ---------- Tutor Dashboard ----------
# tutor/routes.py
from flask import render_template, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from models import db, Class, ClassEnrollment, Assignment, Submission, User, ActivityLog

@bp.route("/tutor/dashboard")
@login_required
def tutor_dashboard():
    # -- Classes for this tutor
    classes = (
        Class.query
        .filter_by(tutor_id=current_user.user_id)
        .order_by(desc(Class.created_at))
        .all()
    )
    kpi_active_classes = len(classes)

    # -- KPI: distinct students across those classes
    kpi_students = (
        db.session.query(func.count(func.distinct(ClassEnrollment.user_id)))
        .join(Class, Class.class_id == ClassEnrollment.class_id)
        .filter(Class.tutor_id == current_user.user_id)
        .scalar() or 0
    )

    # -- KPI: total assignments this tutor has created
    kpi_assignments = (
        db.session.query(func.count(Assignment.assignment_id))
        .join(Class, Class.class_id == Assignment.class_id)
        .filter(Class.tutor_id == current_user.user_id)
        .scalar() or 0
    )

    # -- Precompute class sizes
    class_sizes_sq = (
        db.session.query(
            ClassEnrollment.class_id.label("cid"),
            func.count(ClassEnrollment.user_id).label("size")
        )
        .group_by(ClassEnrollment.class_id)
    ).subquery()

    # -- Recent assignments + submissions count + class size
    rows = (
        db.session.query(
            Assignment.assignment_id,
            Assignment.title,
            Assignment.due_date,
            Class.class_id,
            func.coalesce(class_sizes_sq.c.size, 0).label("class_size"),
            func.count(Submission.submission_id).label("submitted"),
        )
        .join(Class, Assignment.class_id == Class.class_id)
        .outerjoin(Submission, Submission.assignment_id == Assignment.assignment_id)
        .outerjoin(class_sizes_sq, class_sizes_sq.c.cid == Class.class_id)
        .filter(Class.tutor_id == current_user.user_id)
        .group_by(Assignment.assignment_id, Class.class_id, class_sizes_sq.c.size)
        .order_by(desc(Assignment.created_at))
        .limit(10)
        .all()
    )

    assignments_tbl = [
        {
            "title": r.title,
            "due": r.due_date,  # format in template
            "submissions": f"{r.submitted}/{r.class_size}",
            "link": url_for("tutor.assignments"),
        }
        for r in rows
    ]

    # -- Leaderboard (sum of Submission.score)
    leaderboard_rows = (
        db.session.query(
            User.full_name,
            func.coalesce(func.sum(Submission.score), 0).label("xp")
        )
        .join(Submission, Submission.user_id == User.user_id)
        .join(Assignment, Assignment.assignment_id == Submission.assignment_id)
        .join(Class, Class.class_id == Assignment.class_id)
        .filter(Class.tutor_id == current_user.user_id)
        .group_by(User.user_id, User.full_name)
        .order_by(desc("xp"))
        .limit(10)
        .all()
    )

    leaderboard = [{"name": (n or "Student"), "xp": f"{int(xp)} XP"} for (n, xp) in leaderboard_rows]

    # 🔧 Dummy fill if no leaderboard rows
    if not leaderboard:
        leaderboard = [
            {"name": "Shubomi", "xp": "2800 XP"},
            {"name": "Bolaji",  "xp": "2650 XP"},
            {"name": "Denzil",  "xp": "2500 XP"},
        ]

    # -- Recent activity for students in this tutor’s classes
    student_ids_sq = (
        db.session.query(ClassEnrollment.user_id)
        .join(Class, Class.class_id == ClassEnrollment.class_id)
        .filter(Class.tutor_id == current_user.user_id)
    ).subquery()

    recent_acts = (
        ActivityLog.query
        .filter(ActivityLog.user_id.in_(student_ids_sq))
        .order_by(desc(ActivityLog.timestamp))
        .limit(8)
        .all()
    )
    recent = [a.action for a in recent_acts]

    # 🔧 Dummy fill if no activity rows
    if not recent:
        recent = [
            "Shubomi completed Quiz 3 (+300 XP)",
            "Denzel unlocked badge — Mathematical Machine",
            "Bolaji submitted ‘Fractions Basics’",
        ]

    # -- Class cards (title, student count, progress placeholder)
    class_sizes_map = dict(
        db.session.query(class_sizes_sq.c.cid, class_sizes_sq.c.size).all()
    )
    class_cards = [{
    "class_id": c.class_id,          # <-- add this
    "title": c.title,
    "students": class_sizes_map.get(c.class_id, 0),
    "progress": 50,                   # placeholder
} for c in classes]

    # 🔧 Optional: provide dummy cards if tutor has no classes yet
    if not class_cards:
        class_cards = [
            {"title": "Maths — Year 8 Set 2", "students": 24, "progress": 58},
            {"title": "Maths — Year 9 Set 1", "students": 19, "progress": 82},
            {"title": "Maths — Year 7 Set 6", "students": 10, "progress": 35},
        ]

    # 🔧 Optional: provide dummy assignments if none exist yet
    if not assignments_tbl:
        assignments_tbl = [
            {"title": "Fractions Basics", "due": None, "submissions": "0/24", "link": url_for("tutor.assignments")},
            {"title": "Algebra Starter",   "due": None, "submissions": "0/19", "link": url_for("tutor.assignments")},
        ]

    return render_template(
        "tutor/tutor_dashboard.html",
        kpi_active_classes=kpi_active_classes,
        kpi_students=kpi_students,
        kpi_assignments=kpi_assignments,
        classes=class_cards,
        assignments=assignments_tbl,
        recent=recent,
        leaderboard=leaderboard,
    )



# ---------- Assignments ----------
def _assignment_form_with_choices():
    form = AssignmentForm()
    # Classes and resources for the selects
    cls = Class.query.order_by(Class.title.asc()).all()
    res = Resources.query.order_by(Resources.title.asc()).all()
    form.class_id.choices = [(c.class_id, f"{c.title} · Y{c.year_group}") for c in cls]
    form.resource_id.choices = [(r.resource_id, r.title) for r in res]
    return form, cls, res

@bp.route("/assignments", methods=["GET", "POST"])
@login_required
def assignments():
    # One route handles both rendering and creation
    form, classes, resources = _assignment_form_with_choices()

    if form.validate_on_submit():
        a = Assignment(
            title=form.title.data.strip(),
            class_id=form.class_id.data,
            resource_id=form.resource_id.data,
        )
        if form.due_date.data:
            a.due_date = form.due_date.data  # already a datetime from WTForms
        db.session.add(a)
        db.session.commit()
        flash("Assignment created.", "success")
        return redirect(url_for("tutor.assignments"))

    # List existing assignments (newest first)
    items = Assignment.query.order_by(Assignment.created_at.desc()).all()
    delete_form = EmptyForm()
    return render_template(
        "tutor/assignments.html",
        form=form,
        assignments=items,
        classes=classes,
        resources=resources,
        delete_form=delete_form,
    )

@bp.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@login_required
def assignments_delete(assignment_id):
    # CSRF for delete button
    delete_form = EmptyForm()
    if not delete_form.validate_on_submit():
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
    form = ClassForm()

    if form.validate_on_submit():
        c = Class(
            title=form.title.data.strip(),
            subject=form.subject.data.strip(),
            year_group=form.year_group.data,
            tutor_id=current_user.user_id,
        )
        db.session.add(c)
        db.session.commit()
        flash("Class created.", "success")
        return redirect(url_for("tutor.assignments"))

    # (Optional) log errors during dev
    if form.errors:
        print("CLASS FORM ERRORS:", form.errors)

    return render_template("tutor/new_class.html", form=form)

# ---------- Manage Students in Class ----------

# tutor/routes.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, User, Class, ClassEnrollment
from tutor.forms import AddStudentSearchForm, AddStudentConfirmForm

@bp.route("/class/<int:class_id>/students", methods=["GET", "POST"])
@login_required
def manage_students(class_id):
    klass = db.session.get(Class, class_id)
    if not klass or klass.tutor_id != current_user.user_id:
        flash("Class not found.", "error")
        return redirect(url_for("tutor.tutor_dashboard"))

    search_form  = AddStudentSearchForm()
    confirm_form = AddStudentConfirmForm()

    # Always stamp class_id into the search form so it survives POST/GET
    search_form.class_id.data = str(class_id)

    # --- Handle "Add to class" ---
    if "submit_add" in request.form:
        confirm_form.class_id.data = str(class_id)
        if confirm_form.validate_on_submit():
            try:
                uid = int(confirm_form.user_id.data)
            except (TypeError, ValueError):
                flash("Invalid learner.", "error")
                return redirect(url_for("tutor.manage_students", class_id=class_id))

            user = db.session.get(User, uid)
            if not user or user.role != "learner":
                flash("That account isn’t a learner.", "error")
                return redirect(url_for("tutor.manage_students", class_id=class_id))

            exists = ClassEnrollment.query.filter_by(class_id=class_id, user_id=user.user_id).first()
            if exists:
                flash(f"{user.full_name or user.email} is already in this class.", "warn")
            else:
                db.session.add(ClassEnrollment(class_id=class_id, user_id=user.user_id))
                db.session.commit()
                flash(f"Added {user.full_name or user.email} to the class.", "success")

            return redirect(url_for("tutor.manage_students", class_id=class_id))
        else:
            # Most common reason: missing/invalid CSRF or missing user_id
            flash("Couldn’t add the student (form expired or incomplete). Please try again.", "error")
            return redirect(url_for("tutor.manage_students", class_id=class_id))

    # --- Handle search ---
    results = []
    if "submit_search" in request.form and search_form.validate_on_submit():
        qtext = search_form.q.data.strip()
        pat = f"%{qtext}%"
        results = (User.query
                    .filter(User.role == "learner", func.lower(User.full_name).like(func.lower(pat)))
                    .order_by(User.full_name.asc())
                    .limit(10).all())
        if not results:
            flash("No matching students found.", "warn")

    # Current students for the table
    students = (User.query
                .join(ClassEnrollment, ClassEnrollment.user_id == User.user_id)
                .filter(ClassEnrollment.class_id == class_id)
                .order_by(User.full_name.asc())
                .all())

    return render_template(
        "tutor/manage_students.html",
        class_=klass,
        students=students,
        search_form=search_form,
        confirm_form=confirm_form,
        results=results,
    )


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

                #  set metadata 
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
# ----------------- Analytics --------------------
@bp.route("/analytics")
@login_required
def analytics():
    if current_user.role != "tutor":
        flash("Access denied.", "error")
        return redirect(url_for("learner.dashboard"))

    # by subject (from classes)
    by_subject_rows = (
        db.session.query(
            Class.subject.label("subject"),
            func.count(Assignment.assignment_id).label("assignments"),
            func.coalesce(func.avg(Submission.score), 0).label("avg_score"),
        )
        .join(Assignment, Assignment.class_id == Class.class_id)
        .outerjoin(Submission, Submission.assignment_id == Assignment.assignment_id)
        .filter(Class.tutor_id == current_user.user_id)
        .group_by(Class.subject)
        .order_by(Class.subject.asc())
        .all()
    )
    by_subject = [
        {"subject": s or "Unspecified", "assignments": int(a or 0), "avg_score": float(avg or 0)}
        for (s, a, avg) in by_subject_rows
    ]

    # simple leaderboard (same as your dashboard example)
    leaderboard_rows = (
        db.session.query(
            User.full_name,
            func.coalesce(func.sum(Submission.score), 0).label("xp"),
        )
        .join(Submission, Submission.user_id == User.user_id)
        .join(Assignment, Assignment.assignment_id == Submission.assignment_id)
        .join(Class, Class.class_id == Assignment.class_id)
        .filter(Class.tutor_id == current_user.user_id)
        .group_by(User.user_id, User.full_name)
        .order_by(desc("xp"))
        .limit(10)
        .all()
    )
    leaderboard = [{"name": n or "Student", "xp": int(xp)} for (n, xp) in leaderboard_rows]

    return render_template("tutor/analytics.html",
                        by_subject=by_subject,
                        leaderboard=leaderboard)
