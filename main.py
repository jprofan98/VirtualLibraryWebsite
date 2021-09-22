from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FloatField, TextAreaField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.getenv('API_KEY')

# TODO:
#   Implement search by title (search by author?)
# TODO tomorrow:
#   Refactor EVERYTHING
#   Add additional data to Books page
#   Work on Styling?
#   Adjust form validators (make ISBN unchangeable in edit_from_db page)
#   Add "return to default" to edit_from_db page



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book_database.db'
Bootstrap(app)
db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    publisher = db.Column(db.String, nullable=True)
    num_pages = db.Column(db.Integer, nullable=True)
    publish_date = db.Column(db.String, nullable=True)
    author = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=True)


# Creates form to get the ISBN for a book
class ISBNForm(FlaskForm):
    isbn = StringField('ISBN')
    submit = SubmitField('Submit')


class EditForm(FlaskForm):
    isbn = StringField('ISBN', render_kw={'readonly': True})
    title = StringField("Title")
    author = StringField("Author")
    publisher = StringField('Publisher')
    num_pages = StringField('Number of Pages')
    publish_date = StringField('Publish Date')
    description = TextAreaField('Description')
    category = StringField('Category/Genre')
    submit = SubmitField('Submit')


db.create_all()


# Gets book details for a given ISBN
def lookupBook(isbn):

    response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q={isbn}&key={API_KEY}')
    data = response.json()

    try:
        category = data['items'][0]['volumeInfo']['categories'][0]
    except KeyError:
        category = ''

    print(data['items'][0]['selfLink'])
    response = requests.get(data['items'][0]['selfLink'])
    data = response.json()
    filter_criteria = re.compile('<.*?>')
    description = re.sub(filter_criteria, '', data['volumeInfo']['description'])
    book_details = {
        'isbn': data['volumeInfo']['industryIdentifiers'][1]['identifier'],
        'title': data['volumeInfo']['title'],
        'author': data['volumeInfo']['authors'][0],
        'publisher': data['volumeInfo']['publisher'],
        'publish_date': data['volumeInfo']['publishedDate'],
        'num_pages': data['volumeInfo']['pageCount'],
        'description': description,
        'category': category
    }

    return book_details


@app.route('/')
def home():
    book_list = Book.query.all()
    return render_template('index.html', books=book_list)

@app.route('/book')
def load_book():
    id = request.args.get('id')
    book_to_load = Book.query.get(id)
    return render_template('book.html', book = book_to_load)

@app.route('/add', methods=['GET', 'POST'])
def add_by_isbn():
    isbn_form = ISBNForm()
    if request.method == 'POST':
        return redirect(url_for('edit_book', isbn=request.form.get("isbn")))
    return render_template('add.html', form=isbn_form)


@app.route('/edit', methods=['GET', 'POST'])
def edit_book():
    if request.method == 'POST':
        book_to_add = Book(
            isbn=request.form.get('isbn'),
            title=request.form.get('title'),
            publisher=request.form.get('publisher'),
            num_pages=request.form.get('num_pages'),
            publish_date=request.form.get('publish_date'),
            author=request.form.get('author'),
            description=request.form.get('description'),
            category = request.form.get('category')
        )
        db.session.add(book_to_add)
        db.session.commit()

        return redirect(url_for('home'))

    isbn = request.args.get("isbn")
    details = lookupBook(isbn)
    edit_form = EditForm()

    edit_form.isbn.data = isbn
    edit_form.author.data = details['author']
    edit_form.title.data = details['title']
    edit_form.publisher.data = details['publisher']
    edit_form.num_pages.data = details['num_pages']
    edit_form.publish_date.data = details['publish_date']
    edit_form.category.data = details['category']
    edit_form.description.data = details['description']

    return render_template('edit.html', form=edit_form, book=details)


@app.route('/edit_from_db', methods=['GET', 'POST'])
def edit_from_db():
    id = request.args.get('id')
    book_to_edit = Book.query.get(id)

    edit_form = EditForm()



    if request.method == 'POST':
        book_to_edit.isbn = request.form.get('isbn')
        book_to_edit.title = request.form.get('title')
        book_to_edit.publisher = request.form.get('publisher')
        book_to_edit.num_pages = request.form.get('num_pages')
        book_to_edit.category = request.form.get('category')
        book_to_edit.publish_date = request.form.get('publish_date')
        book_to_edit.author = request.form.get('author')
        book_to_edit.description = request.form.get('description')

        db.session.commit()
        return redirect(url_for('home'))

    edit_form.isbn.data = book_to_edit.isbn
    edit_form.author.data = book_to_edit.author
    edit_form.title.data = book_to_edit.title
    edit_form.publisher.data = book_to_edit.publisher
    edit_form.num_pages.data = book_to_edit.num_pages
    edit_form.category.data = book_to_edit.category
    edit_form.publish_date.data = book_to_edit.publish_date
    edit_form.description.data = book_to_edit.description

    return render_template('edit_from_db.html', form=edit_form, book_id=id)


@app.route('/delete')
def delete_book():
    id = request.args.get('id')
    book_to_delete = Book.query.get(id)
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
