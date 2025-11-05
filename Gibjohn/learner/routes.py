from flask import render_template
from . import bp  # <-- use the blueprint

@bp.route("/learner/dashboard")
def dashboard():
    return render_template(
    "learner_dashboard.html",
    level=3, xp=70, maths=65, english=82, science=35 #changable values for testing
    )

@bp.route("/learner/quiz")
def quiz():
    return render_template("quiz.html")