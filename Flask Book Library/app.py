from flask import Flask, jsonify, request, render_template, url_for, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, UserMixin, logout_user, login_required, current_user
from sqlalchemy import case,desc
from form import LoginForm, RegisterForm, Add_bookForm
from API2 import Book, Pagination, Reading
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "static/covers"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.init_app(app)

app.secret_key = 'hej'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_reading(book):
    pagination = Pagination(book, char_per_page=3120)
    pagination.pagination()
    return Reading(pagination)


class Posty(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    author = db.Column(db.String(100))
    text = db.Column(db.String(1000))
    cover = db.Column(db.String(200))

    user_books = db.relationship(
        'UserBook',
        back_populates='book',
    )

    def avg_rating(self):
        if not self.ratings:
            return "brak ocen"
        return sum(r.value for r in self.ratings) / len(self.ratings)
      #  return round(sum(r.value for r in self.ratings) / len(self.ratings), 2)


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posty.id'))

    user = db.relationship('User', backref='ratings')
    post = db.relationship('Posty', backref='ratings')



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    is_author = db.Column(db.Boolean, default=False)
    user_books = db.relationship(
        'UserBook',
        back_populates='user',
        cascade='all, delete-orphan'
    )


class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('posty.id'))
    page = db.Column(db.Integer, default=0)

    user = db.relationship('User', back_populates='user_books')
    book = db.relationship('Posty', back_populates='user_books')


def get_user_book(book_id):
    if not current_user.is_authenticated:
        return None
    return UserBook.query.filter_by(
        user_id=current_user.id,
        book_id=book_id
    ).first()


def ensure_user_book(book_id):
    if not current_user.is_authenticated:
        return None

    ub = get_user_book(book_id)
    if not ub:
        ub = UserBook(user_id=current_user.id, book_id=book_id, page=0)
        db.session.add(ub)
        db.session.commit()
    return ub



def current_reading():
    book_id = session.get("book_id")
    if not book_id:
        return None, None, 0

    post = Posty.query.get(book_id)
    if not post:
        return None, None, 0

    book = Book(post.title, post.author, post.text, post.id)
    reading = create_reading(book)
    total_pages = reading.pagination.number_of_pages
    return book, reading, total_pages


def save_page_to_db(book_id, page):
    if not current_user.is_authenticated:
        return
    ub = ensure_user_book(book_id)
    if ub:
        ub.page = page
        db.session.commit()




@app.route("/")
def home():
    return render_template('home.html')


@app.route("/books", methods=["POST", "GET"])
def all_books():
    posts = Posty.query.order_by(Posty.title).all()

    if request.method == "POST":
        if "book_id" in request.form:
            if not current_user.is_authenticated:
                return redirect(url_for("login"))

            book_id = request.form["book_id"]
            book = Posty.query.get(book_id)

            if book:
                ub = get_user_book(book.id)
                if ub:
                    flash("Book is already added!")
                    return redirect(url_for("all_books"))

                new_user_book = UserBook(user_id=current_user.id, book_id=book.id, page=0)
                db.session.add(new_user_book)
                db.session.commit()
        elif "value" in request.form:
            if not current_user.is_authenticated:
                return redirect(url_for("login"))
            book_id1 = request.form["id"]
            value= request.form["value"]
            rating = Rating.query.filter_by(user_id=current_user.id, post_id=book_id1).first()
            if rating:
                rating.value = value
            else:
                rating = Rating(value=value, user_id=current_user.id, post_id=book_id1)
                db.session.add(rating)

            db.session.commit()
        elif "book_title" in request.form:
            search_title = request.form["book_title"]
            posts = Posty.query.order_by(
                    case((Posty.title.ilike(f"%{search_title}%"), 0), else_=1),
                    Posty.title
                ).all()

    return render_template("books.html", posts=posts)



@app.route("/base")
def alla_books():
    return render_template("base.html")


@app.route("/add_book", methods=['GET', 'POST'])
@login_required
def add_books():
    if not current_user.is_author:
        return "To add books you must become author"

    form=Add_bookForm()
    title = None
    author = None

    if form.validate_on_submit():
        title = form.Title.data
        author = form.Author.data
        text = form.Text.data
        file = form.Cover.data

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))


        new_post = Posty(title=title, author=author, text=text, cover=filename)
        db.session.add(new_post)
        db.session.commit()

    return render_template('add_book.html', title=title, author=author,form=form)


@app.route("/page3")
def page3():
    return render_template('page3.html')


@app.route("/posts")
def posts():
    posts = Posty.query.all()
    return render_template("posts.html", posts=posts)


@app.route("/posts_json")
def posts_json():
    posts = Posty.query.all()
    posts_list = []
    for post in posts:
        posts_list.append({
            "id": post.id,
            "title": post.title,
            "text": post.text,
            "author": post.author
        })

    return jsonify(posts_list)


@app.route("/view_book", methods=["GET", "POST"])
def view_book():
    if request.method == "POST":
        book_id = int(request.form["book_id"])
        session["book_id"] = book_id

        if current_user.is_authenticated:
            ub = ensure_user_book(book_id)
            session["page"] = ub.page if ub else 0
        else:
            session["page"] = 0

    book, reading, total_pages = current_reading()

    if not book:
        return render_template(
            "read_book.html",
            title=None,
            content=None,
            page=0,
            total_pages=0
        )

    page = session.get("page", 0)
    content = reading.pagination.pages[page]

    return render_template(
        "read_book.html",
        title=book.title,
        content=content,
        page=page,
        total_pages=total_pages
    )


@app.route("/next", methods=["GET", "POST"])
def next_page():
    book, reading, total_pages = current_reading()

    if not book:
        return redirect(url_for("view_book"))

    reading.current_page = session.get("page", 0)
    reading.next_page()
    session["page"] = reading.current_page

    save_page_to_db(session.get("book_id"), reading.current_page)

    content = reading.display_page()
    return render_template(
        "read_book.html",
        title=book.title,
        content=content,
        page=reading.current_page,
        total_pages=total_pages
    )


@app.route("/prev", methods=["GET", "POST"])
def prev_page():
    book, reading, total_pages = current_reading()

    if not book:
        return redirect(url_for("view_book"))

    reading.current_page = session.get("page", 0)
    reading.prev_page()
    session["page"] = reading.current_page

    save_page_to_db(session.get("book_id"), reading.current_page)

    content = reading.display_page()
    return render_template(
        "read_book.html",
        title=book.title,
        content=content,
        page=reading.current_page,
        total_pages=total_pages
    )


@app.route("/page", methods=["GET", "POST"])
def given_page():
    book, reading, total_pages = current_reading()

    if not book:
        return redirect(url_for("view_book"))

    change_page_to = int(request.form["page"]) - 1
    if total_pages <= change_page_to or change_page_to < 0:
        return redirect(url_for("view_book"))

    session["page"] = change_page_to
    save_page_to_db(session.get("book_id"), change_page_to)

    page = session.get("page", 0)
    content = reading.pagination.pages[page]

    return render_template(
        "read_book.html",
        title=book.title,
        content=content,
        page=page,
        total_pages=reading.pagination.number_of_pages
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered!")
        return redirect(url_for("home"))

    return render_template("register.html", form=form)





@app.route("/biblioteka", methods=["GET", "POST"])
@login_required
def biblioteka():
    exist = True
    books = current_user.user_books
    if request.method == "POST":
        if "book_id" in request.form:
            book = Posty.query.get(request.form.get("book_id"))
            if book and not get_user_book(book.id):
                ub = UserBook(user_id=current_user.id, book_id=book.id, page=0)
                db.session.add(ub)
                db.session.commit()
            else:
                exist = False

        elif "book_id_d" in request.form:
            book = Posty.query.get(request.form.get("book_id_d"))
            if book:
                ub = get_user_book(book.id)
                if ub:
                    db.session.delete(ub)
                    db.session.commit()

        elif "read_book" in request.form:
            book_id = int(request.form.get("read_book"))
            session["book_id"] = book_id

            ub = get_user_book(book_id)
            session["page"] = ub.page if ub else 0

            return redirect(url_for("view_book"))
        elif "book_title" in request.form:
            search_title = request.form["book_title"]

            books = UserBook.query.join(Posty).filter(
                UserBook.user_id == current_user.id
            ).order_by(
                case((Posty.title.ilike(f"%{search_title}%"), 0), else_=1),
                Posty.title
            ).all()
        elif "by_pages" in request.form:
            books = UserBook.query.join(Posty).filter(
                UserBook.user_id == current_user.id
                 ).order_by(desc(UserBook.page)).all()


    return render_template("biblioteka.html", exist=exist, books=books)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for("home"))

    return render_template("login.html", form=form)

@app.route("/becoming_author")
@login_required
def becoming_author():
    current_user.is_author = True
    db.session.commit()
    flash('You became an author!')
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    logout_user()
    flash('Logged out')
    return redirect(url_for("home"))

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(debug=True)