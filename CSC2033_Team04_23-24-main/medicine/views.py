from flask import Blueprint, render_template, redirect, url_for, flash, render_template_string, current_app as app, \
    request
from extensions import scheduler
from flask_login import login_required, current_user
from flask_mailman import EmailMessage
from extensions import db
from models import Medicine, Dose, User
from medicine.forms import MedicineForm, DoseForm

medicine_blueprint = Blueprint('medicine', __name__, template_folder='templates')


# view medicines
@medicine_blueprint.route("/medicines")
@login_required
def medicines():
    meds = Medicine.query.filter_by(user_id=current_user.id)
    dose = Dose.query.filter_by(med_id=Medicine.id)
    return render_template("medicines/medicines.html", meds=meds, dose=dose, username=current_user.username)


# add medications and store to database
@medicine_blueprint.route("/add_medicine", methods=["GET", "POST"])
@login_required
def add_medicine():
    form = MedicineForm()
    if form.validate_on_submit():
        med = Medicine(user_id=current_user.id,
                       name=form.name.data)
        db.session.add(med)
        db.session.commit()
        return redirect(url_for("medicine.add_dose", med_id=med.id))
    return render_template("medicines/add_medicine.html", form=form)


# function to send a medication reminder to user via email
def send_med_email(medicine, dose):
    with scheduler.app.app_context():
        email_body = render_template_string(medicine_notification_email_html_content, medicine=medicine, dose=dose)
        user = User.query.filter_by(id=medicine.user_id).first()
        print("Sending email")
        message = EmailMessage(subject="Medicine Notification",
                               body=email_body,
                               to=[user.email])
        message.content_subtype = "html"
        message.send()


# add dose and time and store into database
@medicine_blueprint.route("/add_dose/<int:med_id>", methods=["GET", "POST"])
@login_required
def add_dose(med_id):
    if current_user.id != Medicine.query.filter_by(id=med_id).first().user_id:
        flash("Unauthorized area")
        return redirect(url_for("users.profile"))
    form = DoseForm()
    if form.validate_on_submit():
        dose = Dose(med_id=med_id,
                    dose=form.dose.data,
                    time=form.time.data)
        db.session.add(dose)
        db.session.commit()
        medicine = Medicine.query.filter_by(id=med_id).first()
        hour, minute = dose.time.hour, dose.time.minute
        print(f"Hour of send {hour}, Minute of send ={minute}")
        with app.app_context():
            scheduler.add_job(id=f"Send id {dose.id} email", func=send_med_email, args=(medicine, dose),
                              trigger="cron", hour=hour, minute=minute) # set a reminder to send to user via email
        print(scheduler.get_jobs())
        print("added job")
        return redirect(url_for("medicine.medicines"))
    return render_template("medicines/add_dose.html", form=form)


# Delete medication from database
@medicine_blueprint.route("/delete-meds/<int:id>", methods=["GET", "POST"])
@login_required
def delete_meds(id):
    med = Medicine.query.filter_by(id=id).first()

    if request.method == "POST":
        Doses = Dose.query.filter_by(med_id=med.id)
        for dose in Doses:
            scheduler.remove_job(id=f"Send id {dose.id} email")
        # Delete the medication and save to the database.
        db.session.delete(med)
        db.session.commit()

        # Redirect the user to the next view.
        flash("You have successfully deleted the medication.")
        return redirect(url_for("medicine.medicines"))

    # This is a GET request or the form is invalid.
    return render_template("medicines/delete_meds.html")




medicine_notification_email_html_content = """
<p>Hello</p>
<p>You are receiving this email because you have a medicine does soon. </p>
<p>
    You need to take your: {{medicine.name}}
    You need to take: {{dose.dose}}

</p>
<p>
    The dose was set for {{dose.time}}
</p>
<p> If this is not yours, please notify the development team </p>
<p>
    Thank you for using our service
</p>


"""