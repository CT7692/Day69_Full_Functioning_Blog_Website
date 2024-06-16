from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship
from sqlalchemy import Integer, String, Text, select, ForeignKey
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditor, CKEditorField
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import EditForm, RegisterForm, CommentForm, LoginForm

import smtplib
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

Bootstrap5(app)


login_manager = LoginManager()
login_manager.init_app(app)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(db.Model, UserMixin):
    __tablename__ = "Users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name:  Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    posts: Mapped[list["BlogPost"]] = relationship(back_populates="user")
    comments: Mapped[list["Comment"]] = relationship(back_populates="user")


class BlogPost(db.Model):
    __tablename__ = "Blogs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="parent_blog")

class Comment(db.Model):
    __tablename__ = "Comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"))
    user: Mapped["User"] = relationship(back_populates="comments")
    blog_id: Mapped[int] = mapped_column(ForeignKey("Blogs.id"))
    parent_blog: Mapped["BlogPost"] = relationship(back_populates="comments")


with app.app_context():
    db.create_all()



def populate_form(edit_form, blog):
    edit_form.new_title.data = blog.title
    edit_form.new_subtitle.data = blog.subtitle
    edit_form.new_author.data = blog.user.name
    edit_form.new_img_url.data = blog.img_url
    edit_form.new_body.data = blog.body

def get_user(email):
    with Session(app):
        user = db.session.execute(select(User).where(User.email == email)).scalar()
        return user

def admin_logged_in():
    if current_user != None:
        return    current_user.is_authenticated and current_user.id == 1
    else: return False


def admin_only(my_function):
        def wrapper(*args, **kwargs):
            admin_here = admin_logged_in()
            if admin_here:  return my_function(*args, **kwargs)
            else:   return abort(403)
        wrapper.__name__ = my_function.__name__
        return wrapper

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    h1="Register"
    subheading = "Join the community!"
    image = "static/assets/img/register-bg.jpg"
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user = get_user(register_form.new_email.data)
        if user == None:
            hash_pw = generate_password_hash(
                method="pbkdf2:sha256:600000", salt_length=8, password=register_form.new_password.data)

            with Session(app):
                new_user = User(name=register_form.new_name.data,
                                email=register_form.new_email.data,
                                password=hash_pw)
                db.session.add(new_user)
                db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))
        else: flash("User already exists.")
    return render_template("register.html",
                           form=register_form, h1=h1, subheading=subheading, image=image,
                           logged_in=current_user.is_authenticated)





@app.route('/login', methods=['GET', 'POST'])
def login():
    h1 = "Login"
    subheading = "Welcome back!"
    image = "static/assets/img/login-bg.jpg"
    login_form = LoginForm()
    if login_form.validate_on_submit():
        with Session(app):
            user = get_user(login_form.email.data)
            if user != None:
                if check_password_hash(pwhash=user.password, password=login_form.password.data):
                    login_user(user)
                    return redirect(url_for('get_all_posts'))
                else: flash("Incorrect password.")
            else: flash("User does not exist.")
    return render_template("login.html",
                           form=login_form, h1=h1, subheading=subheading, image=image,
                           logged_in=current_user.is_authenticated)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

@app.route('/')
def get_all_posts():
    h1 = "Some Blogs"
    subheading = "A Blog Theme by Start Bootstrap"
    image = "static/assets/img/home-bg.jpg"
    admin_here = admin_logged_in()

    with Session(app):
        blogs = db.session.execute(select(BlogPost).order_by(BlogPost.id)).scalars()
    return render_template("index.html",
                           h1=h1, subheading=subheading, image=image, blogs=blogs,
                           logged_in=current_user.is_authenticated, admin_here=admin_here)


@app.route('/blog/<int:id>', methods=['GET', 'POST'])
def show_post(id):
    if request.method == 'GET':
        gravatar = Gravatar(app, size=35, rating='g', default='retro',
                            force_default=False,force_lower=False, use_ssl=False,
                            base_url=None)

        today = datetime.now().strftime("%B %d, %Y")

        with Session(app):
            blog = db.session.get(BlogPost, id)
            image = blog.img_url
            h1 = blog.title
            subheading = blog.subtitle
            admin_here = admin_logged_in()
            comment_form = CommentForm()
            comments = db.session.execute(select(Comment).where(Comment.blog_id == id)).scalars()

            return render_template("post.html",
                                   blog=blog, image=image, h1=h1, subheading=subheading,
                                   logged_in=current_user.is_authenticated, admin_here=admin_here, comments=comments,
                                   comment_form=comment_form, gravatar=gravatar, today=today)

    elif request.method == 'POST':
        with Session(app):
            blog = db.session.get(BlogPost, id)
            new_comment = Comment(comment=request.form.get("content"),
                                  user_id=current_user.id,
                                  blog_id=blog.id)
            db.session.add(new_comment)
            db.session.commit()
        return redirect(url_for('show_post', id=id))


@app.route('/new-post', methods=['GET', 'POST'])
@admin_only
def add_new_post():
    if request.method == 'GET':
            h1 = "New Post"
            subtitle = "Let's wow the readers!"
            image = "static/assets/img/edit-bg.jpg"
            edit_form = EditForm()
            return render_template(
                "new_form.html", h1=h1, subheading=subtitle,
                image=image, edit_form=edit_form, logged_in=current_user.is_authenticated)

    elif request.method == 'POST':
        with Session(app):
            user = db.session.execute(select(User).where(User.id == current_user.id)).scalar()
            today = datetime.now().strftime("%B %d, %Y")
            new_blog = BlogPost(title=request.form.get('new_title'),
                                subtitle=request.form.get('new_subtitle'),
                                body=request.form.get('new_body'),
                                date=today,
                                user=user,
                                img_url=request.form.get('new_img_url'),
                                user_id=current_user.id)
            db.session.add(new_blog)
            db.session.commit()
        return redirect(url_for('get_all_posts'))

@app.route('/edit-post/<int:id>', methods=['GET', 'POST'])
@admin_only
def edit_post(id):
    if request.method == 'GET':
            edit_form = EditForm()
            h1 = "Edit Post"
            subtitle = "Let's wow the readers!"
            with Session(app):
                blog = db.session.get(BlogPost, id)
                populate_form(edit_form, blog)
                edit_form.new_author.render_kw = {"readonly": True}
                image = blog.img_url
            return render_template("new_form.html",
                                   h1=h1, subheading=subtitle, image=image, edit_form=edit_form,
                                   logged_in= current_user.is_active)

    elif request.method == 'POST':
        with Session(app):
            blog = db.session.get(BlogPost, id)
            blog.title = request.form.get('new_title')
            blog.subtitle = request.form.get('new_subtitle')
            blog.body = request.form.get('new_body')
            blog.user.name = request.form.get('new_author')
            blog.img_url = request.form.get('new_img_url')
            db.session.commit()
        return  redirect(url_for('get_all_posts'))

@app.route('/delete-post/<int:id>')
@admin_only
def delete_post(**kwargs):
        id = kwargs['id']
        with Session(app):
            blog = db.session.get(BlogPost, id)
            db.session.delete(blog)
            db.session.commit()
        return redirect(url_for('get_all_posts'))

@app.route('/about')
def about():
    h1 = "About Me"
    subheading = "This is what I do."
    image = "static/assets/img/about-bg.jpg"
    return render_template(
        "about.html", h1=h1, subheading=subheading, image=image, logged_in = current_user.is_active)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'GET':
        h1 = "Contact Me"
        subheading = "Have questions? I have answers."
        image = "static/assets/img/contact-bg.jpg"
        return render_template(
            'contact.html', h1=h1, subheading=subheading, image=image, logged_in=current_user.is_active)
    elif request.method == 'POST':
        image = "static/assets/img/contact-bg.jpg"
        my_email = "jrydel92@gmail.com"
        pw = os.environ.get('EMAIL_PW')
        full_name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        msg = request.form['msg']
        full_email = (f"Subject: New message from {full_name}\n\n"
                      f"{msg}\n\nReply immediately to {email} or call at {phone}.").encode('utf-8')

        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=my_email, password=pw)
            connection.sendmail(from_addr=my_email, to_addrs=my_email, msg=full_email)
        return render_template("confirmation.html", logged_in=current_user.is_active, image=image)


if __name__ == "__main__":
    app.run(debug=True, port=5003)
