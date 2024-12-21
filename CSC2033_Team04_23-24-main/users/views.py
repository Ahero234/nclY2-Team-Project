import logging

import bcrypt
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, render_template_string
from flask_login import login_user, current_user, logout_user, login_required
from markupsafe import Markup
from datetime import datetime, timedelta
from app import requires_roles
from users.forms import RegisterForm, LoginForm, UpdateForm

from flask_mailman import EmailMessage
from users.forms import RegisterForm, LoginForm, ResetEmailForm, ResetPasswordForm, UpdateForm
from models import db, User, get_recipes, mdb_delete_recipe, DiaryEntry, Medicine

users_blueprint = Blueprint("users", __name__, template_folder="templates")


# Login User to the Website
@users_blueprint.route("/login", methods=["GET", "POST"])  # Route that allows users to log in
def login():
    if current_user.is_authenticated:  # Cannot log in if already logged in
        print("Already logged in")
        return redirect(url_for("main.index"))
    if "tries" not in session:  # Initiates amount of tries a user can have to log in
        session["tries"] = 3
        print("Login initiated")
        print("Test before validate")
    form = LoginForm()  # Gets form
    if form.validate_on_submit():
        print("Valid Form submission")
        user = User.query.filter_by(email=form.email.data).first()  # Searches for user in database
        print(user)
        for user in User.query.filter_by().all():
            print("User: " + str(user))

        if not user or not (user.validate_password(form.password.data) and user.validate_otp(form.pin.data)):
            # If the user doesn't exist, or it does but does not authenticate
            session["tries"] -= 1  # Lower retry count by 1
            if session["tries"] == 0:
                del session["tries"]  # Delete session variable for tries
                flash("Too many login attempts")
                logging.warning("SECURITY - Login Failure and redirect [%s, %s]", form.email.data, request.remote_addr)
                return redirect(url_for("main.index"))  # Redirect to index
            else:
                flash("At least one of the details you entered was incorrect.\nAttempts left: " + str(session["tries"]))
                print(session["tries"])
                logging.warning("SECURITY - Login Failure [%s, %s]", form.email.data, request.remote_addr)
        else:
            print("User validated")
            login_user(user)  # user successfully logged in
            logging.warning("SECURITY - User Login [%s, %s, %s]", current_user.id, current_user.email,
                            request.remote_addr)
            del session["tries"]  # Delete unneeded session variable
            if current_user.is_authenticated:  # Send user to correct redirect depending on their role
                return redirect(url_for("main.index"))

    return render_template("users/login.html", form=form)  # Render form


# Allow users to be registered to the website
@users_blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    print("Going to register")
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        print("Test 1")
        # if this returns a user, then the email already exists in database

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            print("Email already exists")
            flash("Email address already exists")
            return render_template("users/register.html", form=form)

        # create new user with form data and add to database
        print("Making new user")
        new_user = User(email=form.email.data,
                        username=form.username.data,
                        first_name=form.firstname.data,
                        last_name=form.lastname.data,
                        password=form.password.data,
                        height=form.height.data,
                        dob=form.dob.data,
                        role="user")
        print(User)
        for user in User.query.filter_by().all():
            print("User: " + str(user))

        db.session.add(new_user)
        db.session.commit()
        print("Commit")
        for user in User.query.filter_by().all():
            print("User: " + str(user))

        session["email"] = new_user.email
        logging.warning("SECURITY - User registration [%s %s]", form.email.data, request.remote_addr)

        # sends user to login page
        return redirect(url_for("users.setup_2fa"))

    return render_template("users/register.html", form=form)


# Gives a QR code to the user once they are setup to allow for 2FA
@users_blueprint.route("/setup_2fa")
def setup_2fa():
    if "email" not in session:
        return redirect(url_for("main.index"))
    user = User.query.filter_by(email=session["email"]).first()
    if not user:
        return redirect(url_for("main.index"))
    del session["email"]

    return render_template("users/setup_2fa.html", username=user.email, uri=user.get_2fa_uri()), 200, {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"}


# Logout users from the website
@users_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


# Redirect users to login
@users_blueprint.route("/reset")
def reset():
    session["authentication_attempts"] = 0
    return redirect(url_for("users.login"))


# Users profile route. Users can update their details using the form
@users_blueprint.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    form = UpdateForm()
    if form.validate_on_submit():
        # Handle form submission for updating user details
        id = current_user.id
        new_username = form.username.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        try:
            user = User.query.filter_by(id=id).first()
            if user.username != new_username:
                # Update the username if it has changed using method in User model
                user.change_username(new_username)
            user.first_name = first_name
            user.last_name = last_name

            db.session.commit()
            flash("User details updated successfully!")
            return redirect(url_for("users.profile"))  # Redirect back to the profile page
        except Exception as e:
            flash("USERNAME CAN BE CHANGED EVERY 10 MINUTE YOU WILL BE ABLE TO CHANGE IT AGAIN ON " + str(
                datetime.now() + timedelta(minutes=10)))
            return redirect(url_for("users.profile"))
    else:
        # Render the profile page with user details and form errors
        return render_template("users/profile.html",
                               acc_no=current_user.id,
                               email=current_user.email,
                               first_name=current_user.first_name,
                               last_name=current_user.last_name,
                               username=current_user.username,
                               height=current_user.height,
                               dob=current_user.dob, form=form)


# Send an email with a link to reset a password
# Code taken from https://freelancefootprints.substack.com/p/yet-another-password-reset-tutorial
def send_reset_password_email(user):
    reset_password_url = url_for("users.reset_password", token=user.get_reset_token(),
                                 user_id=user.id, _external=True)
    email_body = render_template_string(reset_password_email_html_content, reset_password_url=reset_password_url)

    message = EmailMessage(subject="Reset your password",
                           body=email_body,
                           to=[user.email])
    message.content_subtype = "html"
    message.send()


# Make a request for email password reset
@users_blueprint.route("/reset_request", methods=["GET", "POST"])
def reset_request():
    form = ResetEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_password_email(user)
        flash("If your account exists, a password reset has been sent to it's attached email.")
        return redirect(url_for("users.login"))
    return render_template("users/reset_request.html", title="Reset password", form=form)


# Confirm users want to delete their account
@users_blueprint.route("/delete", methods=["GET", "POST"])
@login_required
def delete_users():
    user = User.query.filter_by(id=current_user.id).first()

    if request.method == "POST":
        # Delete the account and save to the database.

        for recipe in get_recipes():  # iterate through all recipes
            if recipe["created_by"] == user.username:  # if recipe was created by this user
                mdb_delete_recipe(recipe["id"])  # remove recipe from mongo database

        entries = DiaryEntry.query.filter_by(user_id=id)
        for entry in entries:
            db.session.delete(entry)
            db.session.commit()

        meds = Medicine.query.filter_by(user_id=id)
        for med in meds:
            db.session.delete(med)

        db.session.delete(user)
        db.session.commit()

        db.session.commit()

        # Log account deletion.
        logging.warning("Account Deleted [%s, %s, %s]", current_user.id, current_user.email, request.remote_addr)

        # Redirect the user to the next view.
        flash("You have successfully deleted the account.")
        logout_user()
        return redirect(url_for("main.index"))

    # This is a GET request or the form is invalid.
    return render_template("users/delete.html")


# Reset password route where users come from their reset email
# Code taken from https://freelancefootprints.substack.com/p/yet-another-password-reset-tutorial
@users_blueprint.route("/reset_password/<token>/<int:user_id>", methods=["GET", "POST"])
def reset_password(token, user_id):
    user = User.validate_reset_password_token(token, user_id)
    if not user:
        flash("Email expired. Please get another reset email.")
        return redirect(url_for("main.index"))
    form = ResetPasswordForm()
    print("Got form")
    print(user.email)
    if form.validate_on_submit():
        print("Form validated")
        user.password = bcrypt.hashpw(form.new_password.data.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        db.session.commit()
        flash("Password changed successfully!")
        logging.warning("SECURITY - User Password Reset [%s]", request.remote_addr)

        return redirect(url_for("main.index"))
    print(form.errors)
    return render_template("users/change_password.html", form=form)


@users_blueprint.route("/index")
@login_required
def index():
    return render_template("main/index.html", first_name=current_user.first_name, username=current_user.username)


# Content for the password reset email
reset_password_email_html_content = """

<body >
<h3 style="color:#4A7AC1;">4Health Password Reset</h3>  
<p>Hello,</p>
<p>You are receiving this email because you requested a password reset for your account. </p>
<p>
    To reset your password:
    <a style="text-decoration: none" href="{{ reset_password_url }}">Click here </a>
</p>
<p>
    Alternatively you can use the link below
    {{ reset_password_url }}
</p>
<p> If you have not requested a password reset or require assistance, please alert the support team </p>
<p>
    Thank you!
    4Health Support
</p>

<p> Contact: Support@4Health.com </p>



"""