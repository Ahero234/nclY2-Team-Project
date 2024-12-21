from flask import Blueprint, render_template

errors_blueprint = Blueprint("errors", __name__, template_folder="templates")


# Handling 403 error by rendering the appropriate template
@errors_blueprint.errorhandler(403)
def internal_error(error):
    return render_template("errors/403.html"), 403


    # Handling 404 error by rendering the appropriate template
@errors_blueprint.errorhandler(404)
def internal_error(error):
    return render_template("errors/404.html"), 404


    # Handling 500 error by rendering the appropriate template
@errors_blueprint.errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500