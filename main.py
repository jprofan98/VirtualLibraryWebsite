from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


# Creates form to get the ISBN for a book
class ISBNForm(FlaskForm):
    isbn = StringField('ISBN')
    submit = SubmitField('Submit')


# Gets book details for a given ISBN
def lookupBook(isbn):
    # Call openlibrary API to get initial details
    response = requests.get(f'https://openlibrary.org/isbn/{isbn}.json')
    data = response.json()
    authorURL = data['authors'][0]['key']  # Get API endpoint for author
    descriptionURL = data['works'][0]['key']  # Get API endpoint for book description

    book_details = {
        'title': data['title'],
        'publisher': data['publishers'][0],
        'num_pages': data['number_of_pages'],
        'publish_date': data['publish_date']
    }

    # Call author endpoint to get author name for book details
    response = requests.get(f'https://openlibrary.org{authorURL}.json')
    data = response.json()
    book_details['author'] = data['name']

    # Call description endpoint to get book description
    response = requests.get(f'https://openlibrary.org{descriptionURL}.json')
    data = response.json()
    book_details['description'] = data['description']

    return book_details


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/add', methods=['GET', 'POST'])
def add_by_isbn():
    isbn_form = ISBNForm()
    if request.method == 'POST':
        return redirect(url_for('check_book', isbn=request.form.get("isbn")))
    return render_template('add.html', form=isbn_form)


@app.route('/book', methods=['GET', 'POST'])
def check_book():
    isbn = request.args.get("isbn")
    details = lookupBook(isbn)
    return render_template('book.html', book = details)


if __name__ == '__main__':
    app.run(debug=True)
