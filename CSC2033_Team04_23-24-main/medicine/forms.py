from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TimeField
from wtforms.validators import DataRequired


class MedicineForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    submit = SubmitField()


class DoseForm(FlaskForm):
    dose = StringField(validators=[DataRequired()])
    time = TimeField(validators=[DataRequired()])
    submit = SubmitField()