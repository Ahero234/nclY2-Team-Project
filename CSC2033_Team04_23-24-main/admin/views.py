import logging
import random
from flask import Blueprint, render_template, flash, redirect, url_for, request
from sqlalchemy.orm import make_transient

from app import db, requires_roles
from models import User, RecipeRating, get_recipes, unapproved_recipes_exist, mdb_approve_recipe, mdb_delete_recipe
from flask_login import login_required, current_user

from users.forms import RegisterForm

# CONFIG
admin_blueprint = Blueprint('admin', __name__, template_folder='templates')


# view admin profile
@admin_blueprint.route('/admin')
@requires_roles('admin')
@login_required
def admin():
    return render_template('admin/admin.html', name=current_user.first_name)


# view all registered users
@admin_blueprint.route('/view_all_users')
@requires_roles('admin')
@login_required
def view_all_users():
    current_users = User.query.filter_by(role='user').all()

    return render_template('admin/admin.html', name=current_user.first_name, current_users=current_users)


# view all user activity
@admin_blueprint.route('/view_all_activity', methods=['POST'])
@requires_roles('admin')
@login_required
def view_all_activity():
    user_activity = User.query.filter_by(role='user').all()

    return render_template('admin/admin.html', name=current_user.first_name, content=user_activity)


# view last 10 log entries
@admin_blueprint.route('/logs')
@requires_roles('admin')
@login_required
def logs():
    with open("logging.log", "r") as f:
        content = f.read().splitlines()[-10:]
        content.reverse()

    return render_template('admin/admin.html', logs=content, name=current_user.first_name)


# register a new admin
@admin_blueprint.route('/register_admin', methods=['GET', 'POST'])
@requires_roles('admin')
@login_required
def register_admin():
    # create signup form object
    form = RegisterForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # if this returns a user, then the email already exists in database

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            flash('Email address already exists')
            return render_template('users/register.html', form=form)

        # create a new admin with the form data
        new_admin = User(email=form.email.data,
                         username=form.username.data,
                         first_name=form.firstname.data,
                         last_name=form.lastname.data,
                         height=form.height.data,
                         dob=form.dob.data,
                         password=form.password.data,
                         role='admin')

        # add the new admin to the database
        db.session.add(new_admin)
        db.session.commit()
        flash("A new admin has been added successfully")
        logging.warning('SECURITY - Admin registration [%s %s]', form.email.data, request.remote_addr)

        # sends user to home page
        return redirect(url_for('main.index'))
    # if request method is GET or form not valid re-render signup page
    return render_template('users/register.html', form=form)


# delete users from the database
@admin_blueprint.route('/users/<int:id>/delete/', methods=['GET', 'POST'])
@requires_roles('admin')
@login_required
def delete_users(id):
    if id == current_user.id or current_user.role == 'admin':
        user = User.query.filter_by(id=id).first()
    else:
        flash("You don't have the required permissions to access that page!")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        # Delete the account and save to the database.
        db.session.delete(user)

        for recipe in get_recipes():  # iterate through all recipes
            if recipe["created_by"] == user.username:  # if recipe was created by this user
                mdb_delete_recipe(recipe["id"])  # remove recipe from mongo database

        db.session.commit()

        # Log account deletion.
        logging.warning("Account Deleted [%s, %s, %s]", current_user.id, current_user.email, request.remote_addr)

        # Redirect the user to the next view.
        flash("You have successfully deleted the account.")
        return redirect(url_for("admin.admin"))

    # This is a GET request or the form is invalid.
    return render_template("admin/admin_delete.html")


# function for viewing unapproved recipes
@admin_blueprint.route("/unapproved-recipes")
@requires_roles("admin")
@login_required
def unapproved_recipes():

    if not unapproved_recipes_exist():
        print("[DEBUG] No unapproved recipes")
        return render_template("admin/admin.html", name=current_user.first_name, recipes_list="None")

    recipes_list = get_recipes({"state": "unapproved"})

    return render_template("admin/admin.html", name=current_user.first_name, recipes_list=recipes_list)


# function for approving recipes submitted
@admin_blueprint.route("/approve-recipe")
@requires_roles("admin")
@login_required
def approve_recipe():

    qs = str(request.query_string).lower()
    if "id=" in qs:
        try:
            recipe_id = int(request.args.get("id"))
            print("[DEBUG] approving recipe " + str(recipe_id))
            mdb_approve_recipe(recipe_id)
            return redirect(url_for("admin.unapproved_recipes") + "?id=" + str(recipe_id))
        except (KeyError, ValueError):
            return redirect(url_for("admin.unapproved_recipes"))  # invalid id
    else:
        return redirect(url_for("admin.unapproved_recipes"))  # no id


# function for deleting recipes
@admin_blueprint.route("/delete-recipe")
@requires_roles("admin")
@login_required
def delete_recipe():

    qs = str(request.query_string).lower()
    if "id=" in qs:
        try:
            recipe_id = int(request.args.get("id"))
            print("[DEBUG] deleting recipe " + str(recipe_id))
            mdb_delete_recipe(recipe_id)
            return redirect(url_for("admin.unapproved_recipes"))
        except (KeyError, ValueError):
            return redirect(url_for("admin.unapproved_recipes"))  # invalid id
    else:
        return redirect(url_for("admin.unapproved_recipes"))  # no id


# function to delete review
@admin_blueprint.route("/delete-review")
@requires_roles("admin")
@login_required
def delete_review():

    qs = str(request.query_string).lower()
    if "id=" in qs:
        try:
            review_id = int(request.args.get("id"))
            print("[DEBUG] deleting recipe " + str(review_id))
            review = RecipeRating.query.filter_by(id=review_id).first()
            review.review = None
            db.session.commit()
            return redirect(url_for("recipes.view_recipe") + "?id=" + str(review.recipe_id))
        except (KeyError, ValueError):
            return redirect(url_for("recipes.view_recipes"))  # invalid id
    else:
        return redirect(url_for("recipes.view_recipes"))  # no id
