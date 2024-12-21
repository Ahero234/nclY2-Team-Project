from datetime import datetime
import pytest
from models import User


# Test making a new user
def test_new_user():
    user = User(email="heck@test.org", username="tester", password="nyeh", first_name="John", last_name="doe",
                role="user", dob=datetime.now(), height=170)
    assert user.email == "heck@test.org"
    assert user.password != "nyeh"


# Test that the password given in constructor gets hashed
def test_valid_password():
    user = User(email="heck@test.org", username="tester", password="nyeh", first_name="John", last_name="doe",
                role="user", dob=datetime.now(), height=170)
    assert user.validate_password("nyeh")
