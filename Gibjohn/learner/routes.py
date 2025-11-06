from flask import render_template
from . import bp  # <-- use the blueprint

from flask_wtf import FlaskForm

class EmptyForm(FlaskForm):
    pass

@bp.route("/learner/dashboard", methods=["GET", "POST"])
def dashboard():
    form = EmptyForm()
    return render_template(
        "learner_dashboard.html",
        form=form,
        level=3, xp=70, maths=65, english=82, science=35 #changable values for testing
    )

@bp.route("/learner/quiz")
def quiz():
    return render_template("quiz.html")




