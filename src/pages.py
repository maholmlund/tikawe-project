from sqlite3 import IntegrityError
from functools import wraps
import markupsafe
from flask import Flask, request, redirect, session
from flask import render_template, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from db import Db
import config

app = Flask(__name__)
app.secret_key = config.secret_key


@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace(" ", "&nbsp")
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r


@app.route("/", methods=["GET"])
def index():
    if "username" in session:
        posts = Db().get_posts(20, Db().get_user_by_username(session["username"]).id)
        return render_template("index.html", posts=posts, username=session["username"], request=request)
    posts = Db().get_posts(20)
    return render_template("index.html", posts=posts, request=request)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", next=request.args.get("next"))
    if "username" not in request.form or "pwd" not in request.form:
        return "missing username or password", 400
    username = request.form["username"]
    pwd = request.form["pwd"]
    user = Db().get_user_by_username(username)
    if user and check_password_hash(user.pwd_hash, pwd):
        session["username"] = user.username
        if "next" in request.form:
            return redirect(request.form["next"])
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
    if ("username" not in request.form or
            "password1" not in request.form or
            "password2" not in request.form):
        return "missing fields", 400
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

@app.route("/post", methods=["GET", "POST"])
@login_required
def post():
    if request.method == "GET":
        languages = Db().get_languages()
        return render_template("post.html", languages=languages)
    if "language" not in request.form:
        return render_template(
                "post.html",
                languages=Db().get_languages(),
                msg="please select a language")
    language_id = Db().get_language_id(request.form["language"])
    if "data" not in request.form or len(request.form["data"]) == 0:
        return render_template(
                "post.html",
                languages=Db().get_languages(),
                msg="please provide some content")
    data = request.form["data"]
    user_id = Db().get_user_by_username(session["username"]).id
    Db().create_post(data, language_id, user_id)
    return redirect("/")

@app.route("/edit/<post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
    target_post = Db().get_post_by_id(post_id)
    if target_post.username != session["username"]:
        return "invalid user", 403
    if request.method == "GET":
        languages = Db().get_languages()
        return render_template("edit_post.html",
                               languages=languages,
                               default_lang=target_post.language,
                               data=target_post.data)
    data = request.form["data"]
    language_id = Db().get_language_id(request.form["language"])
    Db().update_post_by_id(post_id, data, language_id)
    return redirect("/")

@app.route("/delete/<post_id>", methods=["POST"])
@login_required
def delete(post_id):
    post = Db().get_post_by_id(post_id)
    if post.username != session["username"]:
        return "invalid user", 403
    Db().delete_post_by_id(post_id)
    return redirect("/")

@app.route("/search", methods=["GET"])
def search():
    term = request.args.get("query")
    if "username" in session:
        posts = Db().search_post_by_string(term, 20, Db().get_user_by_username(session["username"]).id)
    else:
        posts = Db().search_post_by_string(term, 20)
    query = request.query_string.decode("utf-8")
    return render_template("search.html", posts=posts, request=request, query=query)

@app.route("/like/<post_id>", methods=["POST"])
@login_required
def like(post_id):
    user_id = Db().get_user_by_username(session["username"]).id
    Db().toggle_like(post_id, user_id)
    if "next" not in request.form:
        return 400, "missing next field"
    # I wish we could do this using javascript...
    query = "" if "query" not in request.form else "?" + str(request.form["query"])
    return redirect(request.form["next"] + query + f"#post-{post_id}")

@app.route("/comments/<post_id>", methods=["GET"])
def comments(post_id):
    comments = Db().get_comments(post_id)
    if "username" in session:
        post = Db().get_post_by_id(post_id, Db().get_user_by_username(session["username"]).id)
        return render_template("comments.html",
                               post=post,
                               comments=comments,
                               hide_link = True,
                               username = session["username"])
    post = Db().get_post_by_id(post_id)
    return render_template("comments.html",
                           post=post,
                           comments=comments,
                           hide_link = True)

@app.route("/new_comment/<post_id>", methods=["POST"])
@login_required
def new_comment(post_id):
    if "data" not in request.form or len(request.form["data"]) == 0:
        post = Db().get_post_by_id(post_id)
        comments = Db().get_comments(post_id)
        return render_template("comments.html",
                               post=post,
                               comments=comments,
                               hide_link = True,
                               username = session["username"],
                               msg="please provide a valid comment")
    user_id = Db().get_user_by_username(session["username"]).id
    Db().create_comment(request.form["data"], user_id, post_id)
    return redirect("/comments/" + post_id)
