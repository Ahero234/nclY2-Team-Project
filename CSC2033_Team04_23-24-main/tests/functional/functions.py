"""This file is for useful functions used by all tests"""


def login_user(test_client, email, password, otp):
    response = test_client.post("/login", data={"email": email, "password": password,
                                                "pin": otp})
    return response
