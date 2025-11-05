# auth/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    SelectField
)
from wtforms.fields import DateField
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Regexp, ValidationError
)


# --- Form definitions + validators ---
# Allow letters, spaces, hyphens, apostrophes; 2–120 chars total
NAME_PATTERN = r"^[A-Za-z][A-Za-z\s\-’']{1,119}$"

def valid_name(form, field):
    text = (field.data or "").strip()
    if not text:
        raise ValidationError("Name is required.")
def strong_password(form, field):
    pw = field.data or ""
    if len(pw) < 10:
        raise ValidationError("Password must be at least 10 characters long.")
    if not any(c.isdigit() for c in pw):
        raise ValidationError("Password must include at least one number.")
    if not any(not c.isalnum() for c in pw):
        raise ValidationError("Password must include at least one symbol.")
    if not any(c.isupper() for c in pw):
        raise ValidationError("Password must include at least one uppercase letter.")

def normalize_name(name: str) -> str:
    return " ".join(part.capitalize() for part in (name or "").split())



def guardian_not_supported(form, field):
    if field.data == "guardian":
        raise ValidationError("Guardian features coming soon.")




# --- Forms ---
class RegisterForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[
            DataRequired(),
            Length(min=2, max=120),
            Regexp(NAME_PATTERN, message="Use letters, spaces, hyphens or apostrophes."),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=10), strong_password],
    )
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    # HTML date inputs send YYYY-MM-DD; DateField parses to a date object.
    DOB = DateField("Date of birth", format="%Y-%m-%d", validators=[DataRequired()])

    role = SelectField("role",
    choices=[("learner","Learner"),("tutor","Tutor"),("guardian","Guardian")],
    validators=[DataRequired(), guardian_not_supported]
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class ProfileForm(FlaskForm):
    full_name = StringField(
        "Full name",
        validators=[
            valid_name,
            Length(min=2, max=49),
            Regexp(NAME_PATTERN, message="Use letters, spaces, hyphens or apostrophes."),
        ],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    submit = SubmitField("Save changes")


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField(
        "New password",
        validators=[DataRequired(), strong_password],
    )
    confirm = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Update password")

class DeleteAccountForm(FlaskForm):
    password = PasswordField("Confirm password", validators=[DataRequired()])
    confirm = BooleanField(
        "I understand this will permanently delete my account",
        validators=[DataRequired()],
    )
    delete_submit = SubmitField("Delete account")
