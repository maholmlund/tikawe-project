import flask
from db import Db


class RegistrationForm:
    def __init__(self, form):
        self.username = form.get("username") if "username" in form else ""
        self.password1 = form.get("password1") if "password1" in form else ""
        self.password2 = form.get("password2") if "password2" in form else ""
        self.errors = []

    def validate(self):
        if len(self.username) < 4:
            self.errors.append("username too short")
        if len(self.password1) < 4:
            self.errors.append("password too short")
        if self.password1 != self.password2:
            self.errors.append("passwords do not match")
        if Db().get_user_by_username(self.username) is not None:
            self.errors.append("username already in use")
        return len(self.errors) == 0


class LoginForm:
    def __init__(self, form):
        self.username = form["username"] if "username" in form else ""
        self.password = form["password"] if "password" in form else ""
        self.next = form["next"] if "next" in form else "/"
        self.errors = []
