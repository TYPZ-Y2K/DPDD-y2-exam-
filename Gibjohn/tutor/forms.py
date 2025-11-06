from flask_wtf import FlaskForm
from wtforms import MultipleFileField, StringField, TextAreaField, SubmitField, URLField, IntegerField, SelectField, DateTimeLocalField
from wtforms.validators import Length, NumberRange
from wtforms.validators import DataRequired, Optional, URL
from flask_wtf.file import FileField, FileAllowed

class ResourceForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    link = URLField("Link (YouTube/Vimeo/Article)", validators=[Optional(), URL()])
    files = MultipleFileField("Files", validators=[Optional(), FileAllowed(['pdf','png','jpg','jpeg','mp4','mov','avi','doc','docx','ppt','pptx'])])
    submit = SubmitField("Add Resource")

class ClassForm(FlaskForm):
    title = StringField("Class Title", validators=[
        DataRequired(), Length(min=2, max=120)
    ])
    subject = StringField("Subject", validators=[
        DataRequired(), Length(min=2, max=80)
    ])
    year_group = IntegerField("Year Group", validators=[
        DataRequired(), NumberRange(min=1, max=13, message="Year must be 1–13")
    ])
    submit = SubmitField("Create Class")

class AssignmentForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=120)])
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    resource_id = SelectField("Resource", coerce=int, validators=[DataRequired()])
    # HTML <input type="datetime-local">
    due_date = DateTimeLocalField("Due date (optional)", format="%Y-%m-%dT%H:%M", validators=[Optional()])
    submit = SubmitField("Add assignment")
