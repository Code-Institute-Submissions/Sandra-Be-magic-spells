import os
from datetime import datetime
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


# Configuration
app = Flask(__name__)

# Passing Mongo database url via environment
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
# Passing Secret Key via environment
app.secret_key = os.environ.get("SECRET_KEY")

# Creating Mongo app
mongo = PyMongo(app)


# Home page
@app.route("/")
@app.route("/home")
def home():
    home = mongo.db.home.find()
    return render_template("home.html", home=home)


# Spell page
@app.route("/get_spells")
def get_spells():
    spells = list(mongo.db.spells.find())
    return render_template("spells.html", spells=spells)


# Magical Tools page
@app.route("/tools")
def tools():
    tools = mongo.db.tools.find()
    return render_template("tools.html", tools=tools)


# Search
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    spells = list(mongo.db.spells.find({"$text": {"$search": query}}))
    return render_template("spells.html", spells=spells)


# Register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Unfortunately username already exists, try different one!")
            return redirect(url_for("register"))

        # check if passwords match
        if request.form.get("password") != request.form.get("confirm-password"):
            flash("Your passwords did not match, please try again!")
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


# Log In page
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


# Profile page
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        spells = list(mongo.db.spells.find({'added_by': username}))
        return render_template("profile.html", username=username, spells=spells)

    return redirect(url_for("login"))


# Log out page
@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


# Add Spell page
@app.route("/add_spell", methods=["GET", "POST"])
def add_spell():
    if request.method == "POST":
        todaydate = datetime.today()
        spell = {
            "category_name": request.form.get("category_name"),
            "spell_title": request.form.get("spell_title"),
            "spell_description": request.form.get("spell_description"),
            "spell_list": request.form.get("spell_list"),
            "spell_process": request.form.get("spell_process"),
            "spell_date": '{0:%d} {0:%B}, {0:%Y}'.format(
                todaydate, "day", "month", "year"),
            "added_by": session["user"]
        }
        mongo.db.spells.insert_one(spell)
        flash("Spell Successfully Added")
        return redirect(url_for("get_spells"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_spell.html", categories=categories)


# Edit Spell page
@app.route("/edit_spell/<spell_id>", methods=["GET", "POST"])
def edit_spell(spell_id):
    if request.method == "POST":
        todaydate = datetime.today()
        submit = {
            "category_name": request.form.get("category_name"),
            "spell_title": request.form.get("spell_title"),
            "spell_description": request.form.get("spell_description"),
            "spell_list": request.form.get("spell_list"),
            "spell_process": request.form.get("spell_process"),
            "spell_date": '{0:%d} {0:%B}, {0:%Y}'.format(
                todaydate, "day", "month", "year"),
            "added_by": session["user"]
        }
        mongo.db.spells.update({"_id": ObjectId(spell_id)}, submit)
        flash("Spell Successfully Updated")

    spell = mongo.db.spells.find_one({"_id": ObjectId(spell_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_spell.html", spell=spell, categories=categories)


# Delete
@app.route("/delete_spell/<spell_id>")
def delete_spell(spell_id):
    mongo.db.spells.remove({"_id": ObjectId(spell_id)})
    flash("Spell Deleted")
    return redirect(url_for("get_spells"))


# Categories page
@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


# Add Category page
@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New Spell Category Added")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


# Edit Category page
@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Spell Category Successfully Updated")
        return redirect(url_for("get_categories"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


# Delete Category page
@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Spell Category Successfully Deleted")
    return redirect(url_for("get_categories"))


# Error Handlers
@app.errorhandler(404)
def response_404(e):
    return render_template("404.html")


# Run the App
# Change debug from True to False before submitting
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)