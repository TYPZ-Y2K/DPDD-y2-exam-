from flask import render_template
from . import bp  # <-- use the blueprint]

@bp.route("/tutor/dashboard")
def tutor_dashboard():
    return render_template("tutor_dashboard.html")

@bp.route("/tutor/manage_learners")
def manage_learners():
    return render_template("manage_learners.html")

@bp.route("/new_assignments")
def new_assignments():
    return render_template("new_assignments.html")