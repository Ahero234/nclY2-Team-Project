import pytest
import pyotp
from models import User
from flask_login import current_user
from tests.functional.functions import login_user
import re
from playwright.sync_api import Page, expect


# Test home page exists.
def test_home_page(client):
    with client as test_client:
        response = test_client.get("/")
        assert response.status_code == 200

# Test register page exists.
def test_register_page_active(client):
    with client as test_client:
        response = test_client.get("/register")
        assert response.status_code == 200

# Test all elements in the register template are present.
def test_register_template(page: Page) -> None:
    page.goto("http://127.0.0.1:5000/")
    page.get_by_role("link", name="Register").click()
    expect(page.get_by_placeholder("First Name")).to_be_empty();
    expect(page.get_by_placeholder("Last Name")).to_be_empty();
    expect(page.get_by_placeholder("Email")).to_be_empty();
    expect(page.get_by_placeholder("Username")).to_be_empty();
    expect(page.get_by_placeholder("Password", exact=True)).to_be_empty();
    expect(page.get_by_placeholder("Confirm Password")).to_be_empty();
    expect(page.get_by_placeholder("DD/MM/YYYY")).to_be_empty();
    expect(page.locator("body")).to_contain_text("Sign up for an account")
    expect(page.locator("#submit")).to_contain_text("Sign up")


# Test if a user is registered in the system correctly.
def test_register_pass(client):
    with client as test_client:
        response = test_client.post("/register",
                                    data={"email": "unittester@test.org", "username": "nyehtest27", "firstname": "John",
                                          "lastname": "Malone", "dob": "02/12/2002", "height": 180,
                                          "password": "Tester123!", "confirm_password": "Tester123!"})
        with test_client.application.app_context():
            created = User.query.filter_by(email="unittester@test.org").first()
            assert created.email == "unittester@test.org"


# Test registering with an invalid email, should fail.
def test_register_invalid_email(client):
    with client as test_client:
        response = test_client.post("/register",
                                    data={"email": "thisisnotanemail", "username": "nyehtest27", "firstname": "John",
                                          "lastname": "Malone", "dob": "02/12/2002", "height": 180,
                                          "password": "Tester123!", "confirm_password": "Tester123!"})

        with test_client.application.app_context():
            created = User.query.filter_by(email="thisisnotanemail").first()
            assert created is None


# Test registering with an invalid date of birth, should fail.
def test_register_invalid_dob(client):
    with client as test_client:
        response = test_client.post("/register",
                                    data={"email": "shouldntpass@test.org", "username": "nyehtest27",
                                          "firstname": "John",
                                          "lastname": "Malone", "dob": "32/12/2002", "height": 180,
                                          "password": "Tester123!", "confirm_password": "Tester123!"})
        with test_client.application.app_context():
            created = User.query.filter_by(email="shouldntpass@test.org").first()
            assert created is None


def test_register_password_filter_fail(client):
    with client as test_client:
        response = test_client.post("/register",
                                    data={"email": "shouldntpass@test.org", "username": "nyehtest27",
                                          "firstname": "John",
                                          "lastname": "Malone", "dob": "21/12/2002", "height": 180,
                                          "password": "password", "confirm_password": "password"})
        with test_client.application.app_context():
            created = User.query.filter_by(email="shouldntpass@test.org").first()
            assert created is None


# Test registering where the password and confirm password field don't match, should fail.
def test_regular_confirm_password_fail(client):
    with client as test_client:
        response = test_client.post("/register",
                                    data={"email": "shouldntpass@test.org", "username": "nyehtest27",
                                          "firstname": "John",
                                          "lastname": "Malone", "dob": "21/12/2002", "height": 180,
                                          "password": "NoJohns21!", "confirm_password": "Incorrect33"})
        with test_client.application.app_context():
            created = User.query.filter_by(email="shouldntpass@test.org").first()
            assert created is None


# Test login page exists
def test_login_page(client):
    with client as test_client:
        response = test_client.get("/login")
        assert response.status_code == 200


# Test login template renders correctly.
def test_login_template(page: Page) -> None:
    page.goto("http://127.0.0.1:5000/")
    page.get_by_role("link", name="Login").click()
    expect(page.locator("body")).to_contain_text("Login to your account")
    expect(page.get_by_placeholder("Email")).to_be_empty();
    expect(page.get_by_placeholder("Password")).to_be_empty();
    expect(page.get_by_placeholder("PIN")).to_be_empty();
    expect(page.locator("form div").filter(has_text="Email").nth(1)).to_be_visible()
    expect(page.locator("form div").filter(has_text="PIN").nth(1)).to_be_visible()
    expect(page.get_by_role("button", name="Login")).to_be_visible()


# Function to neaten tests. Logs in a user with the given arguments.
def login_user(test_client, email, password, otp):
    response = test_client.post("/login", data={"email": email, "password": password,
                                                "pin": otp})
    return response


# Test logging in with an incorrect password. should fail
def test_login_bad_password(client):
    with client as test_client:
        with test_client.application.app_context():
            test_user = User.query.filter_by(email="unittester@test.org").first()
            pin = test_user.pin_key
            otp = pyotp.TOTP(pin).now()
            print(otp)
            # post = test_client.post("/login", data={"email": "unittester@test.org", "password": "This should fail",
            #                                         "pin": otp})
            login_user(test_client, email="unittester@test.org", password="This should fail", otp=otp)

        assert current_user.is_anonymous


# Test logging in with a bad 2fa OTP. Should fail
def test_login_bad_otp(client):
    with client as test_client:
        with test_client.application.app_context():
            login_user(test_client, "unittester@test.org", "Tester123!", 123422)
            assert current_user.is_anonymous


# Test logging in with the correct
def test_login_correct(client):
    with client as test_client:
        with test_client.application.app_context():
            test_user = User.query.filter_by(email="unittester@test.org").first()
            pin = test_user.pin_key
            otp = pyotp.TOTP(pin).now()
            print(otp)
            # post = test_client.post("/login", data={"email": "unittester@test.org", "password": "Tester123!",
            #                                         "pin": otp})
            login_user(test_client, "unittester@test.org", "Tester123!", otp)
        assert current_user.email == "unittester@test.org"


# Test a logged-in user can access the profile
def test_user_profile_get(client):
    with client as test_client:
        with test_client.application.app_context():
            test_user = User.query.filter_by(email="unittester@test.org").first()
            otp = pyotp.TOTP(test_user.pin_key).now()
            login_user(test_client, "unittester@test.org", "Tester123!", otp)
            response = test_client.get("/profile")
            assert response.status_code == 200


# Test a user can change their first name on the profile page
def test_user_profile_change_firstname(client):
    with client as test_client:
        with test_client.application.app_context():
            test_user = User.query.filter_by(email="unittester@test.org").first()
            otp = pyotp.TOTP(test_user.pin_key).now()
            login_user(test_client, "unittester@test.org", "Tester123!", otp)
            response = test_client.post("/profile", data={"first_name": "Jonah", "last_name": test_user.last_name,
                                                          "username": test_user.username, "height": test_user.height})
            updated = User.query.filter_by(email="unittester@test.org").first()
            assert updated.first_name == "Jonah"


def test_user_profile_change_lastname(client):
    with client as test_client:
        with test_client.application.app_context():
            test_user = User.query.filter_by(email="unittester@test.org").first()
            otp = pyotp.TOTP(test_user.pin_key).now()
            login_user(test_client, "unittester@test.org", "Tester123!", otp)
            response = test_client.post("/profile", data={"first_name": test_user.first_name, "last_name": "Smith",
                                                          "username": test_user.username, "height": test_user.height})
            updated = User.query.filter_by(email="unittester@test.org").first()
            assert updated.last_name == "Smith"


def test_user_profile_change_username(client):
    with client as test_client:
        with test_client.application.app_context():
            test_user = User.query.filter_by(email="unittester@test.org").first()
            otp = pyotp.TOTP(test_user.pin_key).now()
            login_user(test_client, "unittester@test.org", "Tester123!", otp)
            response = test_client.post("/profile", data={"first_name": test_user.first_name,
                                                          "last_name": test_user.last_name,
                                                          "username": "Skeletor", "height": test_user.height})
            updated = User.query.filter_by(email="unittester@test.org").first()
            assert updated.username == "Skeletor"


def test_user_profile_change_username_fail(client):
    with client as test_client:
        with test_client.application.app_context():
            test_user = User.query.filter_by(email="unittester@test.org").first()
            otp = pyotp.TOTP(test_user.pin_key).now()
            login_user(test_client, "unittester@test.org", "Tester123!", otp)
            response = test_client.post("/profile", data={"first_name": test_user.first_name,
                                                          "last_name": test_user.last_name,
                                                          "username": "Skeletor!"})
            updated = User.query.filter_by(email="unittester@test.org").first()
            assert updated.username != "Skeletor!"
