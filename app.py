# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import ast
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)

    def insert(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()

    def update(self):
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    website = db.Column(db.String(120))

    def insert(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()

    def update(self):
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'))
    start_time = db.Column(db.DateTime)

    def insert(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()

    def delete(self):
        db.session.delete(self)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()

    def update(self):
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error {e} while trying to commit to database")
            db.session.rollback()


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE, d MMMM y, 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------


@app.route('/venues', methods=['GET', 'POST'])
def venues():
    data = []
    # get all venues
    venues = Venue.query.all()
    # create a set for the locations
    locations = set()

    for venue in venues:
        # add city/state tuples
        locations.add((venue.city, venue.state))

    # for each unique city/state, add venues
    for location in locations:
        data.append({
            "city": location[0],
            "state": location[1],
            "venues": []
        })

    # for each area, add venues to matching city/state
    for venue in venues:
        for area in data:
            if venue.city == area['city'] and venue.state == area['state']:
                area['venues'].append({
                    "id": venue.id,
                    "name": venue.name,
                })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    data = []
    search_term = request.form.get('search_term', '')
    # venues found
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

    for venue in venues:
        num_upcoming_shows = 0
        shows = Show.query.filter_by(id=venue.id).all()

        for show in shows:
            if show.start_time > datetime.now():
                num_upcoming_shows += 1

        data.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_show": num_upcoming_shows
        })

    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    # get venue by id
    venue = Venue.query.filter_by(id=venue_id).first()
    # get all show for a given venue
    shows = Show.query.filter_by(id=venue.id).all()

    def upcoming_shows():
        """return upcoming shows"""
        upcoming = []

        for show in shows:
            if show.start_time > datetime.now():
                upcoming.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                    "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                    "start_time": show.start_time.strftime("%A, %d %B %Y, at %I:%M %p"),
                })
        return upcoming

    def past_shows():
        """return past shows"""
        past = []

        for show in shows:
            if show.start_time < datetime.now():
                past.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                    "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                    "start_time": str(show.start_time)
                })
        return past

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": ast.literal_eval(venue.genres),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows(),
        "upcoming_shows": upcoming_shows(),
        "past_shows_count": len(past_shows()),
        "upcoming_shows_count": len(upcoming_shows()),
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    error = False

    # Get data
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']

    # Create model
    venue = Venue(
        name=name,
        city=city,
        state=state,
        address=address,
        phone=phone,
        genres=genres,
        facebook_link=facebook_link,
        image_link=image_link,
        website=website,
        seeking_talent=seeking_talent,
        seeking_description=seeking_description
    )

    # Update DB
    try:
        venue.insert()
    except Exception:
        error = True

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')


    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    # get all artists
    artists = Artist.query.all()

    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    data = []

    search_term = request.form.get('search_term', '')
    # artists found
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

    for artist in artists:
        num_upcoming_shows = 0
        # get all shows for a given artist
        shows = Show.query.filter_by(artist_id=artist.id).all()

        for show in shows:
            if show.start_time > datetime.now():
                num_upcoming_shows += 1

        data.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows
        })

    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # get artist by id
    artist = Artist.query.filter_by(id=artist_id).first()
    # get all shows for a given artist
    shows = Show.query.filter_by(artist_id=artist_id).all()

    def upcoming_shows():
        """return upcoming shows"""
        upcoming = []

        for show in shows:
            if show.start_time > datetime.now():
                upcoming.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                    "venue_time": show.start_time.strftime("%A, %d %B %Y, at %I:%M %p"),
                })
        return upcoming

    def past_shows():
        """return past shows"""
        past = []

        for show in shows:
            if show.start_time < datetime.now():
                past.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                    "start_time": show.start_time.strftime("%A, %d %B %Y, at %I:%M %p"),
                })
        return past

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": ast.literal_eval(artist.genres),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows(),
        "upcoming_shows": upcoming_shows(),
        "past_shows_count": len(past_shows()),
        "upcoming_shows_count": len(upcoming_shows()),
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    # Get artist data
    artist = Artist.query.filter_by(id=artist_id).first()

    # Fill form with artist data
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    # Get venue data
    venue = Venue.query.filter_by(id=venue_id).first()

    # Fill form
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.website.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False

    # get data
    name = request.form['name']
    city = request.form['city'],
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['description']

    artist = Artist(
        name=name,
        city=city,
        state=state,
        phone=phone,
        genres=genres,
        facebook_link=facebook_link,
        image_link=image_link,
        website=website,
        seeking_venue=seeking_venue,
        seeking_description=seeking_description
    )

    # Update DB
    try:
        artist.insert()
    except Exception:
        error = True

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []

    shows = Show.query.all()

    for show in shows:
        venue_name = Venue.query.filter_by(id=show.venue_id).first().name
        artist_name = Artist.query.filter_by(id=show.artist_id).first().name
        artist_image_link = Artist.query.filter_by(id=show.artist_id).first().image_link

        data.append({
            "venue_id": show.venue_id,
            "venue_name": venue_name,
            "artist_id": show.artist_id,
            "artist_name": artist_name,
            "artist_image_link": artist_image_link,
            "start_time": str(show.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False

    # Get data
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    # Create model
    show = Show(
        artist_id=artist_id,
        venue_id=venue_id,
        start_time=start_time
    )

    # Insert
    try:
        show.insert()
    except Exception:
        error = True

    if error:
        flash('An error occurred. Show could not be listed.')
    else:
        flash('Show was successfully listed!')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
