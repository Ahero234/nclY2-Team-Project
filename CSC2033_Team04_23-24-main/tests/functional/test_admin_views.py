import pytest
import pyotp
from models import User
from flask import redirect, url_for, request
from tests.functional.functions import login_user
import re
from playwright.sync_api import Page, expect


def test_admin_run(client, page: Page) -> None:
    with client as test_client:
        with test_client.application.app_context():
            user = User.query.filter_by(email="admintest@testing.job").first()
            pin= pyotp.TOTP(user.pin_key).now
            # page.goto("http://127.0.0.1:5000/")
            # page.get_by_role("link", name="Login").click()
            # page.get_by_placeholder("Email").click(modifiers=["ControlOrMeta"])
            # page.get_by_placeholder("Email").fill("admintest@testing.job")
            # page.get_by_placeholder("Password").click(modifiers=["ControlOrMeta"])
            # page.get_by_placeholder("Password").fill("Tester456!")
            # page.get_by_placeholder("PIN").click()
            # page.get_by_placeholder("PIN").fill(str((pin))
            # page.get_by_role("button", name="Login").click()
            # expect(page.get_by_role("link", name="Admin")).to_be_visible()
            # expect(page.get_by_role("list")).to_contain_text("Admin")
            # page.get_by_role("link", name="Admin").click()
            # expect(page.get_by_role("heading", name="Current Users")).to_be_visible()
            # expect(page.get_by_role("button", name="View All Users")).to_be_visible()
            # expect(page.get_by_role("main")).to_contain_text("Current Users")
            # expect(page.get_by_role("heading", name="Security Logs")).to_be_visible()
            # expect(page.get_by_role("main")).to_contain_text("Security Logs")
            # expect(page.get_by_role("button", name="Register")).to_be_visible()
            # expect(page.get_by_role("main")).to_contain_text("User Activity Logs")
            # expect(page.get_by_role("button", name="View User Activity")).to_be_visible()

            page.goto("http://127.0.0.1:5000/")
            page.get_by_role("link", name="Login").click()
            page.get_by_placeholder("Email").click()
            page.get_by_placeholder("Email").click()
            page.get_by_placeholder("Email").fill("admintest@testing.job")
            page.locator("form div").filter(has_text="Password").nth(1).click()
            page.get_by_placeholder("Password").fill("Tester456!")
            page.get_by_placeholder("Two-Factor Authentication PIN").click()
            page.get_by_placeholder("Two-Factor Authentication PIN").fill(str((pin)))
            page.get_by_role("button", name="Login").click()
            #expect(page.get_by_role("link", name="Admin")).to_be_visible()
            page.get_by_role("link", name="Admin").click()
            expect(page.get_by_role("heading", name="4Health Admin")).to_be_visible()

            # def test_admin_login_fail(client):
#     with client as test_client:
#         with test_client.application.app_context():
#             test_user = User.query.filter_by(email="usertest@testing.job").first()
#             pin = test_user.pin_key
#             otp = pyotp.TOTP(pin).now()
#             login_user(test_client, test_user.email, "Tester123!", otp)
#             response = test_client.get("/admin", follow_redirects=True)
#             assert request.path != "/admin"



