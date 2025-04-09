from sqlite3 import IntegrityError
from functools import wraps
import markupsafe
from flask import Flask, request, redirect, session, g
from flask import render_template, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from db import Db
from forms import RegistrationForm, LoginForm
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


@app.before_request
def add_user():
    if "username" in session:
        g.user = Db().get_user_by_username(session["username"])
    else:
        g.user = None


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r


@app.route("/", methods=["GET"])
def index():
    if g.user:
        posts = Db().get_posts(60, g.user.id)
    else:
        posts = Db().get_posts(60)
    return render_template("index.html", posts=posts, request=request)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        user = Db().get_user_by_username(form.username)
        if user and check_password_hash(user.pwd_hash, form.password):
            session["username"] = user.username
            return redirect(form.next)
        else:
            form.errors.append("username and password do not match")
    next_url = request.args.get("next")
    if next_url:
        next_url += "?" + \
            request.args["query"] if "query" in request.args else ""
    return render_template("login.html", loginform=form, next=next_url)


@app.route("/logout", methods=["POST"])
def logout():
    if "username" in session:
        del session["username"]
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST":
        if form.validate():
            Db().create_user(form.username, generate_password_hash(form.password1))
            return redirect("/")
    return render_template("register.html", registrationform=form)


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
    Db().create_post(data, language_id, g.user.id)
    return redirect("/")


@app.route("/edit/<post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
    target_post = Db().get_post_by_id(post_id)
    if target_post.username != g.user.username:
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
    if post.username != g.user.username:
        return "invalid user", 403
    Db().delete_post_by_id(post_id)
    return redirect("/")


@app.route("/search", methods=["GET"])
def search():
    term = request.args.get("query")
    if g.user:
        posts = Db().search_post_by_string(
            term, 20, g.user.id)
    else:
        posts = Db().search_post_by_string(term, 20)
    query = request.query_string.decode("utf-8")
    return render_template("search.html",
                           posts=posts,
                           request=request,
                           query=query)


@app.route("/like/<post_id>", methods=["POST"])
@login_required
def like(post_id):
    Db().toggle_like(post_id, g.user.id)
    if "next" not in request.form:
        return 400, "missing next field"
    query = "" if "query" not in request.form else "?" + \
        str(request.form["query"])
    # I wish we could do this using javascript...
    return redirect(request.form["next"] + query + f"#post-{post_id}")


@app.route("/comments/<post_id>", methods=["GET"])
def comments(post_id):
    comments = Db().get_comments(post_id)
    if g.user:
        post = Db().get_post_by_id(
            post_id, g.user.id)
    else:
        post = Db().get_post_by_id(post_id)
    return render_template("comments.html",
                           post=post,
                           comments=comments,
                           hide_link=True)


@app.route("/new_comment/<post_id>", methods=["POST"])
@login_required
def new_comment(post_id):
    if "data" not in request.form or len(request.form["data"]) == 0:
        post = Db().get_post_by_id(post_id)
        comments = Db().get_comments(post_id)
        return render_template("comments.html",
                               post=post,
                               comments=comments,
                               hide_link=True,
                               msg="please provide a valid comment")
    Db().create_comment(request.form["data"], g.user.id, post_id)
    return redirect("/comments/" + post_id)


@app.route("/user/<username>", methods=["GET"])
def user_page(username):
    target_user = Db().get_user_by_username(username)
    post_count = Db().get_user_post_count(target_user.id)
    if "username" in session:
        posts = Db().get_posts_by_user_id(
            target_user.id,
            20,
            current_user_id=g.user.id)
        return render_template("user.html",
                               target_user=username,
                               post_count=post_count,
                               posts=posts)
    posts = Db().get_posts_by_user_id(target_user.id, 20)
    return render_template("user.html",
                           target_user=username,
                           post_count=post_count,
                           posts=posts)
