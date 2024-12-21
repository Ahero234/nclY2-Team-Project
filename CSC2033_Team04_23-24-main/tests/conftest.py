import pytest
from app import create_app
from extensions import db
import os
import time
from threading import Thread, Event
import subprocess
from models import User

# from flask_sqlalchemy import SQLAlchemy


"""Conftest is important for setting up tests. It specifies the configuration of the tests.
It also is the place to define fixtures, which setup the the environment the tests are run in.
The organisation of the testing structure is based on this presentation : https://youtu.be/OcD52lXq0e8
The conftest setup was setup using this page from the documentation:
 https://flask.palletsprojects.com/en/3.0.x/testing/"
 """


# App fixture for getting an instance of the app for testing
@pytest.fixture(scope="session")
def app():
    app = create_app(testing=True)
    app.config.update({"TESTING": True})
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():  # Makes the local database tables
        db.create_all()
        admin = User(email="admintest@testing.job", username="HeMan42"
                     , password="Tester456!", first_name="Chris", last_name="Loud", dob="02/12/2002", role="admin",
                     height=180)
        user = User(email="usertest@testing.job", username="Userman"
                    , password="Tester123!", first_name="John", last_name="Roe", dob="02/12/2002", role="user",
                    height=180)
        db.session.add(admin)
        db.session.commit()
        db.session.add(user)
        db.session.commit()
        yield app
        db.drop_all()
        db.session.remove()
        db.engine.dispose()
        for i in range(0 , 3):  # Cleanup local db
            try:
                if os.path.exists("../instance"):
                    os.remove("../instance/test.db")
                    os.rmdir("../instance")
            except PermissionError:
                time.sleep(1)


# def server_thread(app):
#     print("App running")
#     app.run()


@pytest.fixture()
def client(app):
    return app.test_client()

#
