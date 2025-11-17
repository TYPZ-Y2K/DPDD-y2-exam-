# learner/forms.py
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired

class QuizForm(FlaskForm):
    question1 = RadioField(
        "What is 1/2 + 1/4?",
        choices=[("a","1/4"),("b","1/2"),("c","3/4"),("d","1")],
        validators=[DataRequired(message="Pick an answer")]
    )
    submit = SubmitField("Submit")

# learner/forms.py (or your central forms.py)
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired

class QuizForm(FlaskForm):
    question1 = RadioField(
        "1) What is 1/2 + 1/4?",
        choices=[("A", "3/4"), ("B", "1/4"), ("C", "2/4")],
        validators=[DataRequired()],
    )
    question2 = RadioField(
        "2) Which is the simplified form of 6/8?",
        choices=[("A", "6/8"), ("B", "4/8"), ("C", "3/4")],
        validators=[DataRequired()],
    )
    question3 = RadioField(
        "3) Which fraction is larger?",
        choices=[("A", "3/8"), ("B", "1/2"), ("C", "4/10")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Submit Quiz")
