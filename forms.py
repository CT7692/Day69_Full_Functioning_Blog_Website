from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
class EditForm(FlaskForm):
    new_title = StringField(label="Title", validators=[DataRequired()])
    new_subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    new_author = StringField(label="Your Name", validators=[DataRequired()])
    new_img_url = StringField(label="Image URL", validators=[DataRequired()])
    new_body = CKEditorField(label="Body", validators=[DataRequired()])
    submit = SubmitField("SUBMIT")


class RegisterForm(FlaskForm):
    new_name = StringField(label="Full Name", validators=[DataRequired()])
    new_email = StringField(label="Email", validators=[DataRequired()])
    new_password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField("SUBMIT")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField("SUBMIT")


class CommentForm(FlaskForm):
    content = CKEditorField(label="Comment", validators=[DataRequired()])
    submit = SubmitField("SUBMIT")