import os

from flask import Flask, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import hashlib


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password=(hashlib.md5((request.form.get("password")).encode()))
    password=password.hexdigest()

    if db.execute("SELECT * FROM users WHERE  (username = :username) AND (password=:password)",
            {"username": username, "password": password}).rowcount == 0:
        return render_template("error.html", message="incorrect username or password")

    #check username and password
    db.execute("SELECT username FROM users WHERE  (username = :username) AND (password=:password)",
            {"username": username, "password": password})
    #db.commit()
    return render_template("success.html", username=username)


@app.route("/registerform", methods=["POST"])
def registerform():
    return render_template("registerform.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password=(hashlib.md5((request.form.get("password")).encode()))
    password=password.hexdigest()

    if db.execute("SELECT * FROM users WHERE  (username = :username)",
        {"username": username}).rowcount == 1:
        return render_template("error.html", message="username already existing")

    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
        {"username":username, "password":password})
    db.commit()
    return render_template("success.html", username=username)
