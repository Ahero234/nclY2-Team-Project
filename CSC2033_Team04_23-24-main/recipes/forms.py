from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Length, NumberRange
import re


# title, category, tags, summary, ingredients, instructions, preparation_time, servings, calories_per_serving
class RecipeForm(FlaskForm):
    title = StringField(validators=[DataRequired(message="Please fill in this field."), Length(min=5, max=100)])
    summary = TextAreaField(validators=[DataRequired(message="Please fill in this field.")])
    category = StringField(validators=[DataRequired(message="Please fill in this field.")])
    tags = StringField(validators=[DataRequired(message="Please fill in this field.")])
    ingredients = TextAreaField(validators=[DataRequired(message="Please fill in this field.")])
    instructions = TextAreaField(validators=[DataRequired(message="Please fill in this field.")])
    preparation_time = IntegerField(validators=[DataRequired(message="Please fill in this field."), NumberRange(min=1, max=1440)])
    servings = IntegerField(validators=[DataRequired(message="Please fill in this field."), NumberRange(min=1, max=100)])
    calories_per_serving = IntegerField(validators=[DataRequired(message="Please fill in this field."), NumberRange(min=1, max=2500)])
    private = BooleanField("Private?")
    submit = SubmitField()

    def get_title(self):
        return self.title


class RatingForm(FlaskForm):
    review = TextAreaField()
    rating = IntegerField(validators=[DataRequired(message="Please select a rating"), NumberRange(min=1, max=5)])
    submit = SubmitField()