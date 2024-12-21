from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField, PasswordField, BooleanField, EmailField
from wtforms.fields.numeric import FloatField
from wtforms.validators import DataRequired, Email, ValidationError, Length, EqualTo, InputRequired
import re


# checks if first and last name doesn't contain any special characters
def char_check(form, field):
    invalid_chars = "*?!'^+%&/()=}][{$#@<>"
    for char in field.data:
        if char in invalid_chars:
            raise ValidationError(f"Character {char} is not allowed.")


# checks if email address is in correct format
def valid_email(form, field):
    p = re.compile("\\A[a-zA-Z0-9.+]+@[a-zA-Z0-9.+]+\\.[a-zA-Z0-9.+]+\\Z")
    if not p.match(field.data):
        raise ValidationError("You must enter a valid email address.")


# checks if password contains required characters
def valid_password(form, field):
    p = re.compile(r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[*?!'^+%&/()=}{$#@<>])")
    if not p.match(field.data):
        raise ValidationError("Password must contain at least 1 digit, at least 1 special character, at least 1 "
                              "lowercase and at least 1 uppercase word character")


# checks if date of birth is in correct format
def valid_dob(form, field):
    p = re.compile(r"^(0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012])[- /.](19|20)\d\d$")
    if not p.match(field.data):
        raise ValidationError("Date of Birth must be in the format: DD/MM/YYYY")


# Form for registration
class RegisterForm(FlaskForm):
    email = StringField(validators=[DataRequired(message="Please fill in this field."), valid_email])
    username = StringField(validators=[DataRequired(message="Please fill in this field."), char_check])
    firstname = StringField(validators=[DataRequired(message="Please fill in this field."), char_check])
    lastname = StringField(validators=[DataRequired(message="Please fill in this field."), char_check])
    height = FloatField(validators=[DataRequired(message="Please fill in this field.")])
    dob = StringField(validators=[DataRequired(message="Please fill in this field."), valid_dob])
    password = PasswordField(validators=[DataRequired(message="Please fill in this field."),
                                         Length(min=8, max=15), valid_password])
    confirm_password = PasswordField(validators=[DataRequired(message="Please fill in this field."),
                                                 EqualTo("password", message="Both passwords must match!")])
    recaptcha = RecaptchaField()
    submit = SubmitField()


    def get_username(self):
        return self.username


    def get_password(self):
        return self.password


    def get_submit(self):
        return self.submit


# Form for logging in users
class LoginForm(FlaskForm):
    email = EmailField(validators=[DataRequired(message="Please fill in this field."), valid_email])
    password = PasswordField(validators=[DataRequired(message="Please fill in this field.")])
    pin = StringField(validators=[DataRequired(message="Please fill in this field.")])
    submit = SubmitField()


    # def get_username(self):
    #     return self.username


    def get_password(self):
        return self.password


    def get_submit(self):
        return self.submit


# for changing password
# Code taken from https://freelancefootprints.substack.com/p/yet-another-password-reset-tutorial
class ResetEmailForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Reset password")


# Form for updating user details
class UpdateForm(FlaskForm):
    acc_no = StringField()
    first_name = StringField(validators=[DataRequired(message="Please fill in this field."), char_check, Length(min=1, max=35)])
    last_name = StringField(validators=[DataRequired(message="Please fill in this field."), char_check, Length(min=1, max=35)])
    username = StringField(validators=[DataRequired(message="Please fill in this field."), char_check, Length(min=5, max=20)])
    submit = SubmitField()


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(
        validators=[DataRequired(), Length(min=8, max=15, message="Must be between 8 and 15 characters in length"),
                    valid_password])
    confirm_new_password = PasswordField(
        validators=[DataRequired(), EqualTo("new_password", message="Both new password fields must be equal")])
    submit = SubmitField("Change Password")


