from flask_restful import Resource,Api,reqparse,marshal_with,fields
from werkzeug.exceptions import HTTPException, NotFound
from flask import Flask,make_response,render_template,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import UserMixin
import datetime
import os
import json
from main import Venue,Show,Show_Venue,Booking,User,Admin





app = Flask(__name__)
app.config['SECRET_KEY'] = 'onepieceisreal'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_database.sqlite3'
db = SQLAlchemy(app)
db.init_app(app)
api=None
app.app_context().push()
api = Api(app)

class NotFoundError(HTTPException):
    def __init__(self, status_code, message = ''):
        self.response = make_response(message, status_code)

class BusinessValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)

show_fields = {
    'show_id' : fields.Integer,
    'name' : fields.String,
    'rating' : fields.String,
    'tags' : fields.String,
    'show_time' : fields.DateTime,
    'price' : fields.Integer,
    'image_file':fields.String
}

venue_fields = {
    "venue_id": fields.Integer,
    "name": fields.String,
    "place": fields.String,
    "location": fields.String,
    "capacity": fields.Integer
}

#To store images
app.config['UPLOAD_FOLDER'] = 'static/showimages'
ALLOWED_EXTENSIONS = set(['jpg','png','jpeg'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



#if request.method == "GET":
    #user_id = id
    #return render_template('search.html', user_id=user_id)


class VenueAPI(Resource):
    @marshal_with(venue_fields)
    def get(self, venue_id=None):
        if venue_id is None:
            venue = Venue.query.all()
        else:
            venue = Venue.query.filter(Venue.venue_id == venue_id).scalar()
        return venue

    @marshal_with(venue_fields)
    def put(self, venue_id):
        venue = Venue.query.get(venue_id)
        name = request.form['venue-name']
        place = request.form['venue-place']
        location = request.form['venue-location']
        capacity = request.form['venue-capacity']
        try:
            venue.name = name
            venue.place = place
            venue.location = location
            venue.capacity = capacity
            db.session.commit()
        except:
            return {'message': 'An error occurred while updating the venue'}, 500
        return venue

    @marshal_with(venue_fields)
    def post(self):
        name = request.form['venue-name']
        place = request.form['venue-place']
        location = request.form['venue-location']
        capacity = request.form['venue-capacity']
        sho = Venue(name=name, place=place, location=location, capacity=capacity)
        try:
            db.session.add(sho)
            db.session.commit()
        except:
            return {'message': 'An error occurred while adding the venue'}, 500
        return sho

    @marshal_with(venue_fields)
    def delete(self, venue_id):
        venue = Venue.query.get(venue_id)
        if venue is None:
            raise NotFoundError(status_code=404)
        for sh in venue.shows:
            # show_id = sh.show_id
            show = Show_Venue.query.filter(Show_Venue.show_id == sh.show_id).all()
            for shows in show:
                db.session.delete(shows)
            db.session.commit()
        db.session.delete(venue)
        db.session.commit()
        return "", 200


# SHOW CRUD API
class ShowAPI(Resource):
    @marshal_with(show_fields)
    def get(self, show_id=None):
        if show_id is None:
            show = Venue.query.all()
        else:
            show = Show.query.filter(Show.show_id == show_id).scalar()
        return show

    @marshal_with(show_fields)
    def post(self, venue_id):
        venue = Venue.query.get(venue_id)
        name = request.form['name']
        rating = request.form['rating']
        tags = request.form['tags']
        venue = Venue.query.get(venue_id)
        showtime = request.form['show_time']
        print(showtime)
        # show_ob = datetime.strftime(showtime, '%Y-%m-%dT%H:%M')
        # show_time = datetime.fromisoformat(show_ob)
        # show_ob=datetime.strftime(show,'%Y-%m-%dT%H:%M')
        try:
            show_time = datetime.datetime.fromisoformat(showtime)
        except ValueError:
            return {'message': 'Invalid datetime format'}, 400
        price = request.form['ticketprice']
        file = request.files['image_file']
        # print(file.filename)
        filename = secure_filename(file.filename)
        # print(filename)
        if file and allowed_file(file.filename):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # print(time)
        show = Show(name=name, rating=rating, tags=tags, show_time=show_time, price=price, image_file=filename)
        print(show)
        try:
            db.session.add(show)
            venue.shows.append(show)
            db.session.commit()
        except:
            return {'message': 'An error occurred while adding the show'}, 500
        return show, 201

    @marshal_with(show_fields)
    def put(self, show_id):
        show = Show.query.get(show_id)
        name = request.form['name']
        rating = request.form['rating']
        tags = request.form['tags']
        time = request.form['show_time']
        try:
            show_time = datetime.datetime.fromisoformat(time)
        except ValueError:
            return {'message': 'Invalid datetime format'}, 400
        # show_time = datetime.fromisoformat(time)
        price = request.form['ticketprice']
        file = request.files['image_file']
        filename = secure_filename(file.filename)
        # print(filename)
        if file and allowed_file(file.filename):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        try:
            show.name = name
            show.rating = rating
            show.tags = tags
            show.show_time = show_time
            show.price = price
            db.session.commit()
        except:
            return {'message': 'An error occurred while updating the show'}, 500
        return show, 201

    @marshal_with(show_fields)
    def delete(self, show_id):
        show = Show.query.get(show_id)
        if show is None:
            raise NotFoundError(status_code=404)
        showv = Show_Venue.query.filter(Show_Venue.show_id == show_id).all()
        for sho in showv:
            print(sho.show_id)
            db.session.delete(sho)
        # db.session.commit()
        db.session.delete(show)
        db.session.commit()
        return "", 200


    if __name__ == '__main__':
        app.run(debug=True)














#class ShowAPI(Resource):
 #class ShowList(Resource):
        #def get(self):
            #shows = Show.query.all()
            #return {'shows': [show.json() for show in shows]}

    #api.add_resource(Show, '/shows/<int:show_id>')
    #api.add_resource(ShowList, '/shows')
    # VENUE CRUD API


