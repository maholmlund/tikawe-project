from flask import flash

from db import Db


class RegistrationForm:
    def __init__(self, form):
        self.username = form.get("username") if "username" in form else ""
        self.password1 = form.get("password1") if "password1" in form else ""
        self.password2 = form.get("password2") if "password2" in form else ""

    def validate(self):
        valid = True
        if len(self.username.strip()) < 4:
            flash("username too short", "error")
            valid = False
        if len(self.password1) < 4:
            flash("password too short", "error")
            valid = False
        if self.password1 != self.password2:
            flash("passwords do not match", "error")
            valid = False
        if Db().get_user_by_username(self.username) is not None:
            flash("username already in use", "error")
            valid = False
        return valid


class LoginForm:
    def __init__(self, form):
        self.username = form["username"] if "username" in form else ""
        self.password = form["password"] if "password" in form else ""


class PostForm:
    def __init__(self, form):
        self.language = form["language"] if "language" in form else ""
        self.data = form["data"] if "data" in form else ""
        self.errors = []

    def validate(self):
        valid = True
        if Db().get_language_id(self.language) is None:
            flash("invalid language", "error")
            valid = False
        # apparently some browsers count the number of characters in a
        # text area differently so we put a higher limit here
        if len(self.data) > 3000 or self.data.count("\n") > 30:
            flash("code too long", "error")
            valid = False
        if len(self.data.strip()) == 0:
            flash("empty code not allowed", "error")
            valid = False
        return valid


class CommentForm:
    def __init__(self, form):
        self.data = form["data"] if "data" in form else ""
        self.errors = []

    def validate(self):
        if len(self.data) == 0:
            flash("please provide non-empty comment", "error")
            return False
        return True
