from flask import Flask, request, redirect, session
from flask import render_template
from werkzeug.security import check_password_hash, generate_password_hash
from db import Db
from sqlite3 import IntegrityError
import config

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    if "username" in session:
        return render_template("index.html", username=session["username"])
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    username = request.form["username"]
    pwd = request.form["pwd"]
    user = Db().get_user_by_username(username)
    if user and check_password_hash(user.pwd_hash, pwd):
        session["username"] = user.username 
        return redirect("/")
    return render_template("login.html", msg="invalid username or password")

@app.route("/logout", methods=["POST"])
def logout():
    if "username" in session:
        del session["username"]
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    username = request.form["username"]
    pwd1 = request.form["password1"]
    pwd2 = request.form["password2"]
    if pwd1 != pwd2:
        return render_template("register.html", msg="passwords do not match")
    try:
        Db().create_user(username, generate_password_hash(pwd1))
    except IntegrityError:
        return render_template("register.html", msg="username already in use")
    return redirect("/")
    
