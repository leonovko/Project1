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
        session['username']=result.username
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


@app.route("/books", methods=["POST"])
def books():
    isbn = request.form.get("isbn")
    title = request.form.get("title")
    author = request.form.get("author")

    books = db.execute("SELECT * FROM books WHERE (isbn LIKE :isbn) AND (title LIKE :title) AND (author LIKE :author)",
            {"isbn": "%" + isbn + "%", "title": "%"+ title + "%", "author": "%" + author + "%"}).fetchall()

    return render_template("index.html", books=books)


@app.route("/books/<int:book_id>")
def book(book_id):

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="No such book.")

    reviews= db.execute("SELECT users.username, reviews.rating, reviews.opinion FROM (books INNER JOIN reviews ON books.id=reviews.book_id) INNER JOIN users ON reviews.user_id=users.id WHERE books.id = :id", {"id": book_id}).fetchall()

    user_id_review_exist=db.execute("SELECT id FROM reviews WHERE (user_id = :id) AND (book_id=:book_id)", {"id": session['user_id'], "book_id":book_id}).fetchone()

    return render_template("book.html", book=book, reviews=reviews, user_id_review_exist=user_id_review_exist)



@app.route("/", methods=["POST"])
def addreview():
    rating = request.form.get("rating")
    opinion = request.form.get("opinion")
    user_id = session['user_id']
    book_id = request.form.get("book_id")

    #parsing the rating
    try:
       rating = int(rating)
    except ValueError:
        return render_template("error.html", message="The rating should be an value between 1 and 5, not a text")

    if (rating < 1) or (rating > 5):
        return render_template("error.html", message="The rating should be a value between 1 and 5")


    #Insert the rating in the data base
    db.execute("INSERT INTO reviews (rating, opinion, user_id, book_id) VALUES (:rating, :opinion, :user_id, :book_id )",
        {"rating":rating, "opinion":opinion, "user_id":user_id, "book_id":book_id})
    db.commit()

    #here you should actually call the function book(book_id), but for me it didn't work
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    reviews= db.execute("SELECT users.username, reviews.rating, reviews.opinion FROM (books INNER JOIN reviews ON books.id=reviews.book_id) INNER JOIN users ON reviews.user_id=users.id WHERE books.id = :id", {"id": book_id}).fetchall()
    user_id_review_exist=db.execute("SELECT id FROM reviews WHERE user_id = :id", {"id": session['user_id']}).fetchone()

    return render_template("book.html", book=book, reviews=reviews, user_id_review_exist=user_id_review_exist)
