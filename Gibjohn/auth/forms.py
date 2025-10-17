# auth/forms.py
from dataclasses import field
from flask_wtf import FlaskForm  # base form class
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField  # form fields
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError  # validators
import re  # for regex validation


# --- Form definitions + validators ---
NAME_PATTERN = r"^[A-Za-z][A-Za-z\s\-']{1,48}$"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
NAME_REGEX = re.compile(NAME_PATTERN)
EMAIL_REGEX = re.compile(EMAIL_PATTERN)

def valid_email(form, field):
    value = (field.data or "").strip()
    if not EMAIL_REGEX.match(value):
        raise ValidationError("Enter a valid email address.")


def valid_name(form, field):
    value = (field.data or "").strip()
    if not value or not NAME_REGEX.match(value):
        raise ValidationError("Use letters, spaces, hyphens or apostrophes.")


def normalize_name(name: str) -> str:
    return " ".join(part.capitalize() for part in (name or "").split())


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
    
    
def guardian_not_supported(form, field):
    if field.data == "guardian":
        raise ValidationError("Guardian features coming soon.")




# --- Forms ---
class RegisterForm(FlaskForm):
    name = StringField(
        "name",
        validators=[
            DataRequired(),
            Length(min=2, max=49),
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
    DOB = StringField("Date of Birth", validators=[DataRequired()])

    role = SelectField(
    "role",
    role = SelectField("role",
    choices=[("student","Student"),("tutor","Tutor"),("guardian","Guardian")],
    validators=[DataRequired(), guardian_not_supported])
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class ProfileForm(FlaskForm):
    name = StringField(
        "name",
        validators=[
            valid_name,
            Length(min=2, max=49),
            Regexp(NAME_PATTERN, message="Use letters, spaces, hyphens or apostrophes."),
        ],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), valid_email],
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
