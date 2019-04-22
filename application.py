import os
import hashlib

from flask import Flask, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


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
    if not session.get('logged_in'):
        #return render_template("index.html")
        return render_template("registerform.html")
    else:
        return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password=(hashlib.md5((request.form.get("password")).encode()))
    password=password.hexdigest()

    #check username and password, the one above works as well.
    query=db.execute("SELECT * FROM users WHERE  (username = :username) AND (password=:password)",
            {"username": username, "password": password})
    result=query.first()

    if result:
        session['logged_in'] = True
        session['user_id']=result.id
        return render_template("index.html", username=result.username)
    else:
        return render_template("error.html", message="incorrect username or password")


@app.route("/logout", methods=["POST"])
def logout():
    session['logged_in'] = False
    session['user_id']=[]
    #return render_template("index.html")
    return index()

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
    return render_template("index.html", username=username)


@app.route("/search", methods=["POST"])
def search():
    isbn = request.form.get("isbn")
    title = request.form.get("title")
    author = request.form.get("author")

    books = db.execute("SELECT * FROM books WHERE (isbn = :isbn) or (title=:title) or (author=:author)",
            {"isbn": isbn, "title": title, "author":author}).fetchall()
    return render_template("index.html", books=books)
