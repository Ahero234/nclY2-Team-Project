from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from extensions import db
from models import DiaryEntry
from diary.forms import DiaryEntryForm
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

# Create a blueprint for the diary
diary_blueprint = Blueprint("diary", __name__, template_folder="templates")


# Route for creating a new diary entry or editing an existing one
@diary_blueprint.route("/diary/new", methods=["GET", "POST"])
@diary_blueprint.route("/diary/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def new_entry(entry_id=None):
    if entry_id:
        # Get the diary entry with the provided id
        entry = DiaryEntry.query.get_or_404(entry_id)
        if entry.user_id != current_user.id:
            flash("You are not authorized to view this page!", "danger")
            return redirect(url_for("diary.list_entries"))
        form = DiaryEntryForm(obj=entry)
    else:
        entry = None
        form = DiaryEntryForm()
    # If the form is submitted and validated, create a new diary entry or update an existing one

    if form.validate_on_submit():
        if entry:
            entry.date = form.date.data
            entry.weight = form.weight.data
            entry.calorie_intake = form.calorie_intake.data
            entry.hours_of_sleep = form.hours_of_sleep.data
            entry.steps = form.steps.data
            entry.calorie_burned = form.calorie_burned.data
            entry.diary_log = form.diary_log.data
            db.session.commit()
            flash("Your diary entry has been updated!", "success")
            return redirect(url_for("diary.list_entries"))
        else:
            # Check if a diary entry already exists for the provided date
            existing_entry = DiaryEntry.query.filter_by(date=form.date.data, user_id=current_user.id).first()
            if existing_entry:
                flash("A diary entry already exists for this date!", "danger")
            else:
                entry = DiaryEntry(
                    date=form.date.data,
                    weight=form.weight.data,
                    height=current_user.height,
                    calorie_intake=form.calorie_intake.data,
                    hours_of_sleep=form.hours_of_sleep.data,
                    steps=form.steps.data,
                    calorie_burned=form.calorie_burned.data,
                    diary_log=form.diary_log.data,
                    user_id=current_user.id
                )
                db.session.add(entry)
                db.session.commit()
                flash("Your diary entry has been created!", "success")
        return redirect(url_for("diary.list_entries"))
    return render_template("diary/diary.html", title="Edit Entry" if entry else "New Entry", form=form,
                           legend="Edit Entry" if entry else "New Entry")


# Retrieve all diary entries for the current user
@diary_blueprint.route("/diary")
@login_required
def list_entries():
    # Get all diary entries of the current user
    entries = DiaryEntry.query.filter_by(user_id=current_user.id).all()
    return render_template("diary/list_entries.html", title="Diary Entries", entries=entries)


# Route for visualizing diary entries of the current user
@diary_blueprint.route("/diary/visualize")
@login_required
def visualize_entries():
    entries = DiaryEntry.query.filter_by(user_id=current_user.id).all()
    # If there are entries, create a visualization using matplotlib and render it in a template

    if not entries:
        flash("No diary entries to visualize", "warning")
        return redirect(url_for("diary.list_entries"))

    dates = [entry.date for entry in entries]
    weight = [entry.weight for entry in entries]
    bmi = [entry.bmi for entry in entries]
    calorie_intakes = [entry.calorie_intake for entry in entries]
    calorie_burned = [entry.calorie_burned for entry in entries]
    steps = [entry.steps for entry in entries]
    hours_of_sleep = [entry.hours_of_sleep for entry in entries]

    dates, weights, bmi, calorie_intakes, calorie_burned, steps, hours_of_sleep = zip(*sorted(zip(dates, weight, bmi, calorie_intakes, calorie_burned, steps, hours_of_sleep)))
    # Convert dates to string format
    dates = [date.strftime("%Y-%m-%d") for date in dates]

    # Create a bar chart for each diary entry attribute
    fig, axs = plt.subplots(3, 2, figsize=(15, 15))

    axs[1, 0].bar(dates, weights, color="tab:blue")
    axs[1, 0].set_title("Weight")
    axs[1, 0].set_xlabel("Date")
    axs[1, 0].set_ylabel("Weight (kg)")
    axs[1, 0].tick_params(axis="x", rotation=45)

    axs[0, 1].bar(dates, calorie_intakes, color="tab:orange")
    axs[0, 1].set_title("Calorie Intake")
    axs[0, 1].set_xlabel("Date")
    axs[0, 1].set_ylabel("Calorie Intake (kcal)")
    axs[0, 1].tick_params(axis="x", rotation=45)

    axs[0, 0].bar(dates, calorie_burned, color="tab:green")
    axs[0, 0].set_title("Calorie Burned")
    axs[0, 0].set_xlabel("Date")
    axs[0, 0].set_ylabel("Calorie Burned (kcal)")
    axs[0, 0].tick_params(axis="x", rotation=45)

    axs[1, 1].bar(dates, steps, color="tab:red")
    axs[1, 1].set_title("Steps")
    axs[1, 1].set_xlabel("Date")
    axs[1, 1].set_ylabel("Steps")
    axs[1, 1].tick_params(axis="x", rotation=45)

    axs[2, 0].bar(dates, hours_of_sleep, color="tab:purple")
    axs[2, 0].set_title("Hours of Sleep")
    axs[2, 0].set_xlabel("Date")
    axs[2, 0].set_ylabel("Hours of Sleep")
    axs[2, 0].tick_params(axis="x", rotation=45)

    axs[2, 1].bar(dates, hours_of_sleep, color="tab:cyan")
    axs[2, 1].set_title("BMI")
    axs[2, 1].set_xlabel("Date")
    axs[2, 1].set_ylabel("BMI")
    axs[2, 1].tick_params(axis="x", rotation=45)

    # Adjust layout and add title
    fig.tight_layout()
    plt.suptitle("Diary Entries Visualization", fontsize=16)
    plt.subplots_adjust(top=0.95)

    # Save the plot as a base64 encoded image
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode("utf8")
    plt.close(fig)

    return render_template("diary/visualize.html", title="Visualize Entries", image_base64=image_base64)
