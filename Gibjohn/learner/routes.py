# learner/routes.py
from urllib.parse import parse_qs, urlparse
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from models import db, Class, ClassEnrollment, Assignment, Submission, ActivityLog
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from learner.forms import QuizForm
from models import Submission

from . import bp

class EmptyForm(FlaskForm):
    pass


from urllib.parse import urlparse

def youtube_embed_src(raw_url: str) -> str | None:
    try:
        u = urlparse(raw_url)
        host = u.netloc.replace("www.", "")
        if "youtube.com" in host:
            if u.path == "/watch":
                vid = parse_qs(u.query).get("v", [None])[0]
                return f"https://www.youtube-nocookie.com/embed/{vid}" if vid else None
            if u.path.startswith("/embed/"):
                return f"https://www.youtube-nocookie.com{u.path}"
        if "youtu.be" in host:
            vid = u.path.lstrip("/")
            return f"https://www.youtube-nocookie.com/embed/{vid}"
    except Exception:
        pass
    return None


def auto_enroll_if_needed(user):
    """MVP: if a student has no classes, enrol them to the first class."""
    if not user.is_authenticated or user.role != "learner":
        return
    if not user.enrollments:
        first_class = Class.query.order_by(Class.created_at.asc()).first()
        if first_class:
            db.session.add(ClassEnrollment(class_id=first_class.class_id, user_id=user.user_id))
            db.session.commit()

@bp.route("/learner/dashboard", methods=["GET"])
@login_required
def dashboard():
    form = EmptyForm()
    auto_enroll_if_needed(current_user)

    # Get the student's class ids
    class_ids_q = (db.session.query(ClassEnrollment.class_id)
                .filter(ClassEnrollment.user_id == current_user.user_id))

    # Fetch assignments for those classes
    assignments = (Assignment.query
        .filter(Assignment.class_id.in_(class_ids_q))
        .options(
            joinedload(Assignment.class_),     # a.class_.title
            joinedload(Assignment.resource),   # a.resource.title
        )
        # Order: due soonest first; undated ones after; then newest created
        .order_by(Assignment.due_date.is_(None), Assignment.due_date.asc(), desc(Assignment.created_at))
        .limit(10)
        .all()
    )

    return render_template(
        "learner/learner_dashboard.html",  # ensure the folder prefix is correct
        form=form,
        assignments=assignments,
        # demo numbers you were using
        level=3, xp=70, maths=65, english=82, science=35,
    )


@bp.route("/lesson/<int:assignment_id>")
@login_required
def lesson(assignment_id):
    a = (Assignment.query
        .options(joinedload(Assignment.class_), joinedload(Assignment.resource))
        .get(assignment_id))
    if not a:
        flash("Lesson not found.", "error")
        return redirect(url_for("learner.dashboard"))

    # Build one MVP quiz and give it a working Start URL
    quizzes = [{
        "title": "Quiz 1: Fractions Basics",
        "difficulty": "Easy",
        "xp": 50,
        "start_url": url_for("learner.quiz", assignment_id=assignment_id),
    }]

    # Build a YouTube thumbnail if the resource is a YT link
    yt = (a.resource.url or "") if (a.resource and a.resource.type == "link") else ""
    vid = None
    if "youtu.be/" in yt:
        vid = yt.rsplit("/", 1)[-1].split("?")[0]
    elif "youtube.com/watch" in yt and "v=" in yt:
        vid = parse_qs(urlparse(yt).query).get("v", [None])[0]
    thumb_url = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg" if vid else None

    return render_template(
        "learner/lesson.html",
        assignment=a,
        quizzes=quizzes,
        level=3, xp=70,
        thumb_url=thumb_url
    )
@bp.route("/lesson/<int:assignment_id>/play")
@login_required
def play_lesson(assignment_id):
    a = db.session.get(Assignment, assignment_id)
    if not a:
        flash("Lesson not found.", "error")
        return redirect(url_for("learner.dashboard"))
    embed_src = None
    if a.resource and a.resource.type == "link" and a.resource.url:
        embed_src = youtube_embed_src(a.resource.url)

    return render_template(
        "learner/player.html",
        assignment=a,
        embed_src=embed_src,
        level=3,
        xp=70,
    )
# --- FINISH PAGES ---
@bp.route("/lesson/<int:assignment_id>/complete", methods=["GET"])
@login_required
def lesson_complete(assignment_id):
    a = db.session.get(Assignment, assignment_id)
    if not a:
        flash("Lesson not found.", "error")
        return redirect(url_for("learner.dashboard"))

    # Log simple activity + (optional) award XP in your own system later
    db.session.add(ActivityLog(
        user_id=current_user.user_id,
        action=f"Finished lesson — {a.title} (+30 XP)"
    ))
    db.session.commit()

    return render_template(
        "learner/lesson_complete.html",
        assignment=a,
        xp_award=30
    )



@bp.route("/lesson/<int:assignment_id>/quiz", methods=["GET", "POST"])
@login_required
def quiz(assignment_id):
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        flash("Quiz not found.", "error")
        return redirect(url_for("learner.dashboard"))

    form = QuizForm()
    if form.validate_on_submit():
        # Answer key for MVP
        key = {"question1": "A", "question2": "C", "question3": "B"}
        given = {
            "question1": form.question1.data,
            "question2": form.question2.data,
            "question3": form.question3.data,
        }
        correct = sum(1 for k in key if given.get(k) == key[k])
        total = 3
        score_pct = round((correct / total) * 100)

        # Save a submission row
        sub = Submission(
            assignment_id=assignment.assignment_id,
            user_id=current_user.user_id,
            status="submitted",
            score=score_pct,
        )
        db.session.add(sub)
        db.session.commit()

        # Render finish page with results
        return render_template(
            "learner/quiz_finish.html",
            assignment=assignment,
            correct=correct,
            total=total,
            score=score_pct,
            xp_awarded=score_pct,  # simple MVP: XP == % score
        )

    return render_template("learner/quiz.html", assignment=assignment, form=form)
