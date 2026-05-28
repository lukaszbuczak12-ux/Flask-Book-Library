from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileAllowed



class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")




class LoginForm(FlaskForm):
    username = StringField(" username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class Add_bookForm(FlaskForm):
    Title = StringField(" Title", validators=[DataRequired()])
    Author = StringField("Author", validators=[DataRequired()])
    Text = StringField("Text", validators=[DataRequired()])
    Cover = FileField("Cover", validators=[FileAllowed(['jpg', 'png'])])

    submit = SubmitField("Add book")