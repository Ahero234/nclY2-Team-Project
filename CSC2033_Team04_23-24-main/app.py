import os
import logging
from extensions import db, scheduler
from functools import wraps
from flask_talisman import Talisman
from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_qrcode import QRcode
from flask_login import LoginManager, current_user
from flask_mailman import Mail

load_dotenv()

"""Create app function. Makes and returns an instance
of the flask app. This can then be run with app.run()"""
def create_app(testing=False):
    # Create a Flask application instance
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    if testing:  # Use a local sqlite database for testing.
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
        print("Testing mode DB")
    else:  # Else connect to external db as normal
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_ECHO"] = os.getenv("SQLALCHEMY_ECHO")
    app.config["SQLALCHEMY_TRACK_MODIFICATION"] = os.getenv("SQLALCHEMY_TRACK_MODIFICATION")
    app.config["RECAPTCHA_PUBLIC_KEY"] = os.getenv("RECAPTCHA_PUBLIC_KEY")
    app.config["RECAPTCHA_PRIVATE_KEY"] = os.getenv("RECAPTCHA_PRIVATE_KEY")
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")  # Connect to mongo database
    app.config["MAIL_SERVER"]=os.getenv("MAIL_SERVER")  # Get Flask-Mailman configs
    app.config["MAIL_PORT"]=os.getenv("MAIL_PORT")
    app.config["MAIL_USERNAME"]=os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"]=os.getenv("MAIL_PASSWORD")
    app.config["MAIL_USE_TLS"]=os.getenv("MAIL_USE_TLS")
    app.config["MAIL_DEFAULT_SENDER"]=os.getenv("MAIL_DEFAULT_SENDER")
    app.config["RESET_PASS_TOKEN_MAX_AGE"] = os.getenv("RESET_PASS_TOKEN_MAX_AGE")
    app.config["SCHEDULER_API_ENABLED"] = os.getenv("SCHEDULER_API_ENABLED") == True
    # Initialize the database with the Flask application
    db.init_app(app)
    # if testing:
    #     with app.app_context():
    #         db.create_all()
    migrate = Migrate(app, db)
    # Initialize QRcode with the Flask application
    QRcode(app)
    # Initialize Mail with the Flask application
    Mail(app)
    # Start scheduler
    scheduler.init_app(app)
    scheduler.start()


    class SecurityFilter(logging.Filter):
        # Check if the log message contains "SECURITY"
        def filter(self, record):
            return "SECURITY" in record.getMessage()


    # Get logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Logger level is DEBUG

    # file handler
    file_handler = logging.FileHandler(os.path.join(os.path.dirname(__file__), "logging.log"), "a")
    file_handler.setLevel(logging.WARNING)
    file_handler.addFilter(SecurityFilter())

    formatter = logging.Formatter("%(asctime)s : %(message)s", "%m/%d/%Y %I:%M:%S %p")
    file_handler.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(file_handler)

    # Import blueprints for use in the system
    from main.views import main_blueprint
    from recipes.views import recipes_blueprint
    from diary.views import diary_blueprint
    from users.views import users_blueprint
    from admin.views import admin_blueprint
    from medicine.views import medicine_blueprint
    from errors.views import errors_blueprint
    from medicine.views import medicine_blueprint

    #Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(recipes_blueprint)
    app.register_blueprint(diary_blueprint)
    app.register_blueprint(users_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(medicine_blueprint)
    app.register_blueprint(errors_blueprint)

    # set up login manager
    login_manager = LoginManager()
    login_manager.login_view = "users.login"
    login_manager.init_app(app)

    from models import User, ChangeUsernameLog


    """Load users into the system"""
    @login_manager.user_loader
    def load_user(id):
        if id is None or id == "None":
            print("id = None")
            id = -1
        print("id type = " + str(type(id)) + " and value = " + str(id))
        return User.query.get(int(id))


    # Custom error page handling
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template("errors/400.html"), 400


    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403


    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404


    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500


    @app.errorhandler(503)
    def unavailable_service_error(error):
        return render_template("errors/503.html"), 503

    return app


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                logging.warning("SECURITY - Unauthorised access [%s %s %s %s]",
                                current_user.id,
                                current_user.email,
                                current_user.role,
                                request.remote_addr)
                return render_template("errors/403.html")
            return f(*args, **kwargs)

        return wrapped

    return wrapper


if __name__ == "__main__":
    app = create_app()
    # setup_error_handling(app)
    app.run()
