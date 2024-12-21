from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, FloatField, SubmitField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length


# Create a form for the diary entry
class DiaryEntryForm(FlaskForm):

    date = DateField("Date", validators=[DataRequired()])
    weight = FloatField("Weight (kg)", validators=[DataRequired(), NumberRange(min=1)])
    calorie_intake = IntegerField("Calorie Intake", validators=[DataRequired(), NumberRange(min=1)])
    hours_of_sleep = FloatField("Hours of Sleep", validators=[DataRequired(), NumberRange(min=0, max=24)])
    steps = IntegerField("Steps", validators=[DataRequired(), NumberRange(min=1)])
    calorie_burned = IntegerField("Calorie Burned", validators=[DataRequired(), NumberRange(min=1)])
    diary_log = TextAreaField("Diary Log", validators=[DataRequired(), Length(max=200)])
    submit = SubmitField("Save Entry")


# Compare this snippet from users/views.py:
# from flask import Blueprint, render_template, redirect, url_for, flash
# from flask_login import login_user, current_user, logout_user, login_required
# from users.forms import RegisterForm, LoginForm
# from users.models import User
# from models import db
#
# users_blueprint = Blueprint("users", __name__, template_folder="templates")
#
#
# @users_blueprint.route("/register", methods=["GET", "POST"])
# def register():
