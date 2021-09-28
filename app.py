import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_spells")
def get_spells():
    spells = list(mongo.db.spells.find())
    return render_template("spells.html", spells=spells)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Unfortunately username already exists, try different one!")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Congratulations! Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Oops! Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Oops! Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_spell", methods=["GET", "POST"])
def add_spell():
    if request.method == "POST":
        spell = {
            "category_name": request.form.get("category_name"),
            "spell_title": request.form.get("spell_title"),
            "spell_description": request.form.get("spell_description"),
            "spell_list": request.form.get("spell_list"),
            "spell_process": request.form.get("spell_process"),
            "spell_date": request.form.get("spell_date"),
            "added_by": session["user"]
        }
        mongo.db.spells.insert_one(spell)
        flash("Spell Successfully Added")
        return redirect(url_for("get_spells"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_spell.html", categories=categories)


@app.route("/edit_spell/<spell_id>", methods=["GET", "POST"])
def edit_spell(spell_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "spell_title": request.form.get("spell_title"),
            "spell_description": request.form.get("spell_description"),
            "spell_list": request.form.get("spell_list"),
            "spell_process": request.form.get("spell_process"),
            "spell_date": request.form.get("spell_date"),
            "added_by": session["user"]
        }
        mongo.db.spells.update({"_id": ObjectId(spell_id)}, submit)
        flash("Spell Successfully Updated")

    spell = mongo.db.spells.find_one({"_id": ObjectId(spell_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_spell.html", spell=spell, categories=categories)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)