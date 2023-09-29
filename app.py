from flask import Flask, render_template, redirect, url_for, request, session, g
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import sqlite3
import random
import string


class NameForm(FlaskForm):
    name = StringField("What is your name?", validators=[DataRequired()])
    submit = SubmitField("Submit")


app = Flask(__name__)
app.config["SECRET_KEY"] = "hard to guess string"


def get_db():
    if getattr(g, "_database", None) is None:
        g._database = sqlite3.connect("databases/data.db")

    return g._database


@app.teardown_appcontext
def close_db(*args):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


with open("schema.sql") as file, app.app_context():
    get_db().executescript(file.read())


@app.route("/", methods=["GET", "POST"])
def index():
    form = NameForm()
    if form.validate_on_submit():
        cursor = get_db().cursor()
        cursor.execute("SELECT session FROM users WHERE name = $1", (form.name.data,))
        user = cursor.fetchone()
        if user is None:
            # create new user with the form.name.data and a random session id
            id = "".join([random.choice(string.ascii_letters) for _ in range(64)])

            cursor.execute(
                "INSERT INTO users(name, session) VALUES($1, $2)", (form.name.data, id)
            )
            session["known"] = False
        else:
            session["known"] = True

        session["name"] = form.name.data
        form.name.data = ""
        return redirect(url_for("index"))
    return render_template(
        "index.jinja",
        form=form,
        name=session.get("name"),
        known=session.get("known", False),
    )


@app.route("/user/<name>")
def user(name):
    return render_template("user.jinja", name=name)
