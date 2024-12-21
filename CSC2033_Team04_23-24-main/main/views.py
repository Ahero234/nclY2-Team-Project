from flask import Blueprint, render_template

main_blueprint = Blueprint("main", __name__, template_folder="templates")


# This method handles the route "/" and renders the "main/index.html" template.
@main_blueprint.route("/")
def index():
    return render_template("main/index.html")