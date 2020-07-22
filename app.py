#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for,jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import JSON
import sys
import os
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate=Migrate(app,db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(JSON)
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default = True)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    shows = db.relationship('Show',cascade="all,delete-orphan", backref='venue', lazy=True)
  
class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(JSON)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default = True)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    shows = db.relationship('Show',cascade="all,delete-orphan", backref='artist', lazy=True)

class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer , primary_key=True)
    venue_id = db.Column(db.Integer , db.ForeignKey('venues.id'), nullable = False)
    artist_id = db.Column(db.Integer , db.ForeignKey('artists.id'), nullable = False)
    start_time = db.Column(db.DateTime, nullable=False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

def upcoming_shows_count(shows):
  current_time= datetime.now()
  upcoming_shows_count=0
  for show in shows:
    if show.start_time>current_time:
      upcoming_shows_count+=1
  return upcoming_shows_count
def past_shows_count(shows):
  current_time= datetime.now()
  past_shows_count=0
  for show in shows:
    if show.start_time<current_time:
      past_shows_count+=1
  return past_shows_count
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venue_orders = Venue.query.order_by(Venue.state,Venue.city).all()
  data=[]
  state_p=[]
  city_p=[]
  venue=[]
  for venue_order in venue_orders:
    if city_p==venue_order.city and state_p==venue_order.state:
      venue.append({
        "id": venue_order.id,
        "name": venue_order.name
      })
    else:
      venue=[{
        "id": venue_order.id,
        "name": venue_order.name
      }]
      data.append({
        "city": venue_order.city,
        "state": venue_order.state,
        "venues": venue
      })
    city_p=venue_order.city
    state_p=venue_order.state
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  search= request.form.get('search_term')
  data=[]
  p=0
  venues=Venue.query.filter(Venue.name.ilike('%{}%'.format(search)))
  for venue in venues:
    shows=Show.query.filter(Show.venue_id==venue.id).all()
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": upcoming_shows_count(shows)
    })
    p+=1
  response={
    "count":p,
    "data":data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  current_time= datetime.now()
  shows=Show.query.filter(Show.venue_id==venue_id).all()
  upcoming_shows=[]
  past_shows=[]
  for show in shows:
    if show.start_time>current_time:
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link":Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time":str(show.start_time)
      })
    else:
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link":Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time":str(show.start_time)
      })
  venues=Venue.query.all()
  for venue in venues:
    if venue.id==venue_id:
      data={
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "facebook_link": venue.facebook_link,
        "website": venue.website,
        "image_link": venue.image_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "upcoming_shows": upcoming_shows,
        "past_shows": past_shows,
        "past_shows_count":past_shows_count(shows),
        "upcoming_shows_count":upcoming_shows_count(shows),
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
  form = VenueForm(request.form)
  error=False
  try:
    name=request.form.get('name')
    city=request.form.get('city')
    address=request.form.get('address')
    state=request.form.get('state')
    phone=request.form.get('phone')
    facebook_link=request.form.get('facebook_link')
    genres=request.form.getlist('genres')
    website=request.form.get('website')
    seeking_talent=request.form.get('seeking_talent')
    if seeking_talent is 'y':
      seeking_talent=True
    else:
      seeking_talent=False
    seeking_description=request.form.get('seeking_description')
    image_link=request.form.get('image_link')
    venue = Venue(name=name, city=city, address=address, state=state, 
    phone=phone, facebook_link=facebook_link, genres=genres, website=website,
    seeking_talent=seeking_talent, seeking_description=seeking_description, image_link=image_link)
    db.session.add(venue)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    else:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error=False
  try:
    venue=Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error: 
      flash('An error occurred. Venue could not be deleted.')
    else:
      flash('Venue  was successfully deleteded!')
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists=Artist.query.all()
  data=[]
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search= request.form.get('search_term')
  data=[]
  p=0
  artists=Artist.query.filter(Artist.name.ilike('%{}%'.format(search)))
  for artist in artists:
    shows=Show.query.filter(Show.artist_id==artist.id).all()
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": upcoming_shows_count(shows)
    })
    p+=1
  response={
    "count":p,
    "data":data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  current_time= datetime.now()
  shows=Show.query.filter(Show.artist_id==artist_id).all()
  upcoming_shows=[]
  past_shows=[]
  for show in shows:
    if show.start_time>current_time:
      upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
        "venue_image_link":Venue.query.filter_by(id=show.artist_id).first().image_link,
        "start_time":str(show.start_time)
      })
    else:
      past_shows.append({
        "venue_id": show.venue_id,
        "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
        "venue_image_link":Venue.query.filter_by(id=show.venue_id).first().image_link,
        "start_time":str(show.start_time)
      })
  artists=Artist.query.all()
  for artist in artists:
    if artist.id==artist_id:
      data={
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "website": artist.website,
        "image_link": artist.image_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "upcoming_shows": upcoming_shows,
        "past_shows": past_shows,
        "upcoming_shows_count": upcoming_shows_count(shows),
        "past_shows_count": past_shows_count(shows),
      }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist =Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist=Artist.query.get(artist_id)
  error=False
  try:
    artist.name=request.form.get('name')
    artist.city=request.form.get('city')
    artist.state=request.form.get('state')
    artist.phone=request.form.get('phone')
    artist.facebook_link=request.form.get('facebook_link')
    artist.genres=request.form.getlist('genres')
    artist.website=request.form.get('website')
    artist.seeking_venue=request.form.get('seeking_venue')
    if artist.seeking_venue is 'y':
      artist.seeking_venue=True
    else:
      artist.seeking_venue=False
    artist.seeking_description=request.form.get('seeking_description')
    artist.image_link=request.form.get('image_link')
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
    else:
      flash('Artist ' + request.form['name'] + ' was successfully edited!')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue =Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue=Venue.query.get(venue_id)
  error=False
  try:
    venue.name=request.form.get('name')
    venue.city=request.form.get('city')
    venue.address=request.form.get('address')
    venue.state=request.form.get('state')
    venue.phone=request.form.get('phone')
    venue.facebook_link=request.form.get('facebook_link')
    venue.genres=request.form.getlist('genres')
    venue.website=request.form.get('website')
    venue.seeking_talent=request.form.get('seeking_talent')
    if venue.seeking_talent is 'y':
      venue.seeking_talent=True
    else:
      venue.seeking_talent=False
    venue.seeking_description=request.form.get('seeking_description')
    venue.image_link=request.form.get('image_link')
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Venue ' + form.name.data + ' could not be edited.')
    else:
      flash('Venue ' + request.form['name'] + ' was successfully edited!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error=False
  form = ArtistForm(request.form)
  try:
    name=request.form.get('name')
    city=request.form.get('city')
    state=request.form.get('state')
    phone=request.form.get('phone')
    facebook_link=request.form.get('facebook_link')
    genres=request.form.getlist('genres')
    website=request.form.get('website')
    seeking_venue=request.form.get('seeking_venue')
    if seeking_venue is 'y':
      seeking_venue=True
    else:
      seeking_venue=False
    seeking_description=request.form.get('seeking_description')
    image_link=request.form.get('image_link')
    artist = Artist(name=name, city=city, state=state, phone=phone,
    facebook_link=facebook_link, genres=genres, website=website,
    seeking_venue=seeking_venue, seeking_description=seeking_description, image_link=image_link)
    db.session.add(artist)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:     
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    else:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  error=False
  try:
    artist=Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error: 
      flash('An error occurred. Artist could not be deleted.')
    else:
      flash('Artist  was successfully deleteded!')
    return render_template('pages/home.html')
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows=Show.query.all()
  data=[]
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": Venue.query.filter_by(id=show.venue_id).first().name ,
      "artist_id": show.artist_id,
      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name ,
      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link ,
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
  error=False
  try:
    artist_id=request.form.get('artist_id')
    venue_id=request.form.get('venue_id')
    start_time=request.form.get('start_time')
    show = Show(artist_id=artist_id,venue_id=venue_id,start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:flash('An error occurred. Show could not be listed.')
    else:flash('Show was successfully listed!')
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:

if __name__ == '__main__':
    app.run(host='0.0.0.0')
# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0')
'''
