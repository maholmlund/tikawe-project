from flask import Flask, request, redirect, session
from flask import render_template
from werkzeug.security import check_password_hash
from db import Db
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