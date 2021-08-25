from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import InputRequired, NumberRange
import requests
import os

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_DETAIL_URL = "https://api.themoviedb.org/3/movie/"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Configure app
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies-list.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


# Form
class EditForm(FlaskForm):
    rating = FloatField('Your Rating Out of 10 e.g. 7.5', validators=[
        InputRequired(), 
        NumberRange(0, 10, message='Enter the number between 0 and 10.')
    ])
    review = StringField('Your Review', validators=[InputRequired()])
    submit = SubmitField('Done')

class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[InputRequired()])
    submit = SubmitField('Add Movie')
    


# Index of website
@app.route("/")
def home():
    # Order ranking by rating
    all_movies = Movie.query.order_by(Movie.title).all()
    for i in range(1, len(all_movies)+1):
        all_movies[i-1].ranking = i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


# Edit rating and review
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    form = EditForm()
    movie_id = request.args.get('id')
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        # Update
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
        
    return render_template('edit.html', movie=movie_to_update, form=form)


# Delete the database row
@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


# Add new movie and redirect to movies list page
@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(TMDB_SEARCH_URL, params={
            "api_key": TMDB_API_KEY, 
            "query": movie_title
        })
        data = response.json()["results"]

        return render_template('select.html', movies=data)

    return render_template('add.html', form=form)


# Movies list, add new row of data to database and redirect to edit(rating) page
@app.route('/find')
def find_movie():
    # Get movie detail from api id
    movie_api_id = request.args.get('id')
    response = requests.get(f"{TMDB_DETAIL_URL}/{movie_api_id}", params={
        "api_key": TMDB_API_KEY,
        "language": "en-US"
    })
    data = response.json()

    # Add new movie to the database
    new_movie = Movie(
        title=data["title"],
        year=data["release_date"].split("-")[0],
        description=data["overview"],
        img_url=f"{TMDB_IMAGE_URL}/{data['backdrop_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
