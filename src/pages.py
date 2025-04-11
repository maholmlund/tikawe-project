from sqlite3 import IntegrityError
from functools import wraps
from math import ceil
import markupsafe
from flask import Flask, request, redirect, session, g, abort
from flask import render_template, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from db import Db
from forms import RegistrationForm, LoginForm, PostForm, LikeForm, CommentForm
import config
from secrets import token_hex

app = Flask(__name__)
app.secret_key = config.secret_key

ITEMS_PER_PAGE = 20


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


@app.before_request
def check_csrf():
    if request.method == "POST":
        if ("csrf_token" not in request.form or
            "csrf_token" not in session or
                session["csrf_token"] != request.form["csrf_token"]):
            abort(403)


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r


class Pager:
    def __init__(self, n_pages, current_page, link_base, query=""):
        self.n_pages = n_pages if n_pages > 0 else 1
        self.current = current_page
        self.next_page_link = None
        if len(query) != 0:
            query = "?" + query
        if current_page < n_pages:
            self.next_page_link = link_base + str(current_page + 1) + query
        self.prev_page_link = None
        if current_page > 1:
            self.prev_page_link = link_base + str(current_page - 1) + query


@app.route("/", methods=["GET"])
@app.route("/<int:page_id>", methods=["GET"])
def index(page_id=1):
    n_pages = int(ceil(Db().get_post_count() / ITEMS_PER_PAGE))
    if page_id > n_pages:
        abort(404)
    pager = Pager(n_pages, page_id, "/")
    if g.user:
        posts = Db().get_posts(ITEMS_PER_PAGE, (page_id - 1) * ITEMS_PER_PAGE, g.user.id)
    else:
        posts = Db().get_posts(ITEMS_PER_PAGE, (page_id - 1) * ITEMS_PER_PAGE)
    return render_template("index.html", posts=posts, request=request, pager=pager)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        user = Db().get_user_by_username(form.username)
        if user and check_password_hash(user.pwd_hash, form.password):
            session["username"] = user.username
            session["csrf_token"] = token_hex(16)
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
    form = PostForm(request.form)
    if request.method == "POST":
        if form.validate():
            language_id = Db().get_language_id(form.language)
            Db().create_post(form.data, language_id, g.user.id)
            return redirect("/")
    return render_template("post.html", postform=form, languages=Db().get_languages())


@app.route("/edit/<post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
    form = PostForm(request.form)
    target_post = Db().get_post_by_id(post_id)
    if not target_post:
        abort(404)
    if target_post.username != g.user.username:
        return "invalid user", 403
    if request.method == "POST":
        if form.validate():
            language_id = Db().get_language_id(form.language)
            Db().update_post_by_id(post_id, form.data, language_id)
            return redirect("/")
    languages = Db().get_languages()
    form.data = target_post.data
    form.language = target_post.language
    return render_template("edit_post.html",
                           languages=languages,
                           postform=form)


@app.route("/delete/<post_id>", methods=["POST"])
@login_required
def delete(post_id):
    post = Db().get_post_by_id(post_id)
    if not post:
        abort(404)
    if post.username != g.user.username:
        return "invalid user", 403
    Db().delete_post_by_id(post_id)
    return redirect("/")


@app.route("/search", methods=["GET"])
@app.route("/search/<int:page_id>", methods=["GET"])
def search(page_id=1):
    term = request.args.get("query")
    if g.user:
        posts = Db().search_post_by_string(
            term, ITEMS_PER_PAGE, (page_id - 1) * ITEMS_PER_PAGE, g.user.id)
    else:
        posts = Db().search_post_by_string(
            term, ITEMS_PER_PAGE, (page_id - 1) * ITEMS_PER_PAGE)
    query = request.query_string.decode("utf-8")
    n_pages = int(ceil(Db().get_search_match_count(term) / ITEMS_PER_PAGE))
    if page_id > n_pages:
        abort(404)
    pager = Pager(n_pages, page_id, f"/search/", query)
    return render_template("search.html",
                           posts=posts,
                           request=request,
                           pager=pager,
                           query=query)


@app.route("/like/<post_id>", methods=["POST"])
@login_required
def like(post_id):
    form = LikeForm(request.form)
    if not Db().get_post_by_id(post_id):
        abort(404)
    Db().toggle_like(post_id, g.user.id)
    # I wish we could do this using javascript...
    return redirect(form.next + form.query + f"#post-{post_id}")


@app.route("/comments/<post_id>", methods=["GET"])
@app.route("/comments/<post_id>/<int:page_id>", methods=["GET"])
def comments(post_id, page_id=1):
    n_pages = int(ceil(Db().get_comment_count(post_id) / ITEMS_PER_PAGE))
    if not Db().get_post_by_id(post_id) or page_id > n_pages:
        abort(404)
    pager = Pager(n_pages, page_id, f"/comments/{post_id}/")
    comments = Db().get_comments(post_id, ITEMS_PER_PAGE, (page_id - 1) * ITEMS_PER_PAGE)
    form = CommentForm(request.form)
    if g.user:
        post = Db().get_post_by_id(
            post_id, g.user.id)
    else:
        post = Db().get_post_by_id(post_id)
    return render_template("comments.html",
                           post=post,
                           comments=comments,
                           commentform=form,
                           pager=pager,
                           hide_link=True)


@app.route("/new_comment/<post_id>", methods=["POST"])
@login_required
def new_comment(post_id):
    if not Db().get_post_by_id(post_id):
        abort(400)
    form = CommentForm(request.form)
    if form.validate():
        Db().create_comment(form.data, g.user.id, post_id)
        return redirect("/comments/" + post_id)
    post = Db().get_post_by_id(post_id)
    comments = Db().get_comments(post_id)
    return render_template("comments.html",
                           post=post,
                           comments=comments,
                           hide_link=True,
                           commentform=form)


@app.route("/user/<username>", methods=["GET"])
@app.route("/user/<username>/<int:page_id>", methods=["GET"])
def user_page(username, page_id=1):
    target_user = Db().get_user_by_username(username)
    if not target_user:
        abort(404)
    post_count = Db().get_user_post_count(target_user.id)
    n_pages = int(ceil(post_count / ITEMS_PER_PAGE))
    if page_id > n_pages:
        abort(404)
    pager = Pager(n_pages, page_id, f"/user/{username}/")
    if "username" in session:
        posts = Db().get_posts_by_user_id(
            target_user.id,
            ITEMS_PER_PAGE,
            (page_id - 1) * ITEMS_PER_PAGE,
            current_user_id=g.user.id)
        return render_template("user.html",
                               target_user=username,
                               post_count=post_count,
                               pager=pager,
                               posts=posts)
    posts = Db().get_posts_by_user_id(target_user.id,
                                      ITEMS_PER_PAGE, (page_id - 1) * ITEMS_PER_PAGE)
    return render_template("user.html",
                           target_user=username,
                           post_count=post_count,
                           pager=pager,
                           posts=posts)
