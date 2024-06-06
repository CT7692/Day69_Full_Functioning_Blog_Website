from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import Integer, String, Text, select
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import datetime

import smtplib
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap5(app)
ckeditor = CKEditor()
ckeditor.init_app(app)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

class EditForm(FlaskForm):
    new_title = StringField(label="Title", validators=[DataRequired()])
    new_subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    new_author = StringField(label="Your Name", validators=[DataRequired()])
    new_img_url = StringField(label="Image URL", validators=[DataRequired()])
    new_body = CKEditorField(label="Body", validators=[DataRequired()])
    submit = SubmitField('Submit')

def populate_form(edit_form, blog):
    edit_form.new_title.data = blog.title
    edit_form.new_subtitle.data = blog.subtitle
    edit_form.new_author.data = blog.author
    edit_form.new_img_url.data = blog.img_url
    edit_form.new_body.data = blog.body


@app.route('/')
def get_all_posts():
    h1 = "Some Blogs"
    subheading = "A Blog Theme by Start Bootstrap"
    image = "static/assets/img/home-bg.jpg"

    with Session(app):
        blogs = db.session.execute(select(BlogPost).order_by(BlogPost.id)).scalars()

    return render_template("index.html", h1=h1, subheading=subheading, image=image, blogs=blogs)

@app.route('/blog/<int:id>')
def show_post(id):
    with Session(app):
        blog = db.session.get(BlogPost, id)
        image = blog.img_url
        h1 = blog.title
        subheading = blog.subtitle
    return render_template("post.html",
                           blog=blog, image=image, h1=h1, subheading=subheading)


@app.route('/new-post', methods=['GET', 'POST'])
def add_new_post():
    if request.method == 'GET':
        h1 = "New Post"
        subtitle = "Let's wow the readers!"
        image = "static/assets/img/edit-bg.jpg"
        edit_form = EditForm()
        return  render_template(
            "new_form.html", h1=h1, subheading=subtitle,
            image=image, edit_form=edit_form)

    elif request.method == 'POST':
        today = datetime.now().strftime("%B %d, %Y")
        new_blog = BlogPost(title=request.form.get('new_title'),
                            subtitle=request.form.get('new_subtitle'),
                            body=request.form.get('new_body'),
                            date=today,
                            author=request.form.get('new_author'),
                            img_url=request.form.get('new_img_url'))
        with Session(app):
            db.session.add(new_blog)
            db.session.commit()
        return redirect(url_for('get_all_posts'))


@app.route('/edit-post/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    if request.method == 'GET':
        edit_form = EditForm()
        h1 = "Edit Post"
        subtitle = "Let's wow the readers!"
        with Session(app):
            blog = db.session.get(BlogPost, id)
            populate_form(edit_form, blog)
            image = blog.img_url
        return render_template("new_form.html", h1=h1, subheading=subtitle, image=image, edit_form=edit_form)
    elif request.method == 'POST':
        today = datetime.now().strftime("%B %d, %Y")
        with Session(app):
            blog = db.session.get(BlogPost, id)
            blog.title = request.form.get('new_title')
            blog.subtitle = request.form.get('new_subtitle')
            blog.body = request.form.get('new_body')
            blog.author = request.form.get('new_author')
            blog.img_url = request.form.get('new_img_url')
            db.session.commit()
        return  redirect(url_for('get_all_posts'))


@app.route('/delete-post/<int:id>')
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
    return render_template("about.html", h1=h1, subheading=subheading, image=image)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'GET':
        h1 = "Contact Me"
        subheading = "Have questions? I have answers."
        image = "static/assets/img/contact-bg.jpg"
        return render_template(
            'contact.html', h1=h1, subheading=subheading, image=image)
    elif request.method == 'POST':
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
        return render_template("confirmation.html")



if __name__ == "__main__":
    app.run(debug=True, port=5003)
