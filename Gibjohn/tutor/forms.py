from flask_wtf import FlaskForm
from wtforms import MultipleFileField, StringField, TextAreaField, SubmitField, URLField
from wtforms.validators import DataRequired, Optional, URL
from flask_wtf.file import FileField, FileAllowed

class ResourceForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    link = URLField("Link (YouTube/Vimeo/Article)", validators=[Optional(), URL()])
    files = MultipleFileField("Files", validators=[Optional(), FileAllowed(['pdf','png','jpg','jpeg','mp4','mov','avi','doc','docx','ppt','pptx'])])
    submit = SubmitField("Add Resource")

