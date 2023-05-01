import os

import matplotlib
import matplotlib.pyplot as plt
from flask import Flask, render_template, redirect, url_for, request, make_response, flash
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from flask_restful import Resource, Api, marshal_with, fields
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Length

matplotlib.use('Agg')
import base64
from io import BytesIO
from datetime import datetime
import datetime



app = Flask(__name__)
app.config['SECRET_KEY'] = 'onepieceisreal'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_database.sqlite3'
db = SQLAlchemy(app)
db.init_app(app)
bootstrap = Bootstrap(app)
app.app_context().push()
api = Api(app)
#Login Handlers
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'





#ERRORS
class BusinessValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(message, status_code)

class NotFoundError(HTTPException):
    def __init__(self, status_code, message = ''):
        self.response = make_response(message, status_code)



venue_fields = {
    "venue_id": fields.Integer,
    "name": fields.String,
    "place": fields.String,
    "location": fields.String,
    "capacity": fields.Integer
}

show_fields = {
    'show_id' : fields.Integer,
    'name' : fields.String,
    'rating' : fields.String,
    'tags' : fields.String,
    'show_time' : fields.DateTime,
    'price' : fields.Integer,
    'image_file':fields.String
}


#To store images
app.config['UPLOAD_FOLDER'] = 'static/showimages'
ALLOWED_EXTENSIONS = set(['jpg','png','jpeg'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#API
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
        try:
            show_time = datetime.datetime.fromisoformat(showtime)
        except ValueError:
            return {'message': 'Invalid datetime format'}, 400
        price = request.form['ticketprice']
        file = request.files['image_file']
        filename = secure_filename(file.filename)
        if file and allowed_file(file.filename):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
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
        price = request.form['ticketprice']
        file = request.files['image_file']
        filename = secure_filename(file.filename)
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
        db.session.delete(show)
        db.session.commit()
        return "", 200

















#TABLES TO POPULATE USER, ADMIN, SHOWS , VENUES AND BOOKING
class Show_Venue(db.Model):
    __tablename__='show_venue'
    show_venue_id=db.Column(db.Integer,primary_key=True,autoincrement=True )
    show_id=db.Column(db.Integer, db.ForeignKey('show.show_id'))
    venue_id= db.Column(db.Integer, db.ForeignKey('venue.venue_id'))

class Booking(UserMixin,db.Model):
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, unique=False)
    show_id = db.Column(db.Integer, nullable=False)
    seats= db.Column(db.Integer, nullable=False)


class User(UserMixin,db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String(50), unique=True)

class Admin(UserMixin,db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String(50), unique=True)

class Venue(db.Model):
    venue_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    place  = db.Column(db.String(120), nullable=False)
    location = db.Column(db.Text, nullable=False)
    capacity = db.Column(db.Text, nullable=False)
    #shows = db.relationship('Show', secondary=show_venue, backref=db.backref('Venue', lazy=True))
    shows = db.relationship('Show',secondary='show_venue')

class Show(db.Model):
    show_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.String(120), nullable=False)
    tags = db.Column(db.String(120), nullable=False)
    show_time = db.Column(db.DateTime)
    price = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120))
    venues = db.relationship('Venue', secondary='show_venue')

    def __init__(self, name: object, rating: object, tags: object, show_time: object, price: object,image_file: object) -> object:
        self.name = name
        self.rating = rating
        self.tags = tags
        self.show_time = show_time
        self.price = price
        self.image_file= image_file

    def json(self):
        return {'show_id': self.show_id, 'name': self.name, 'rating': self.rating, 'tags': self.tags,
                'show_time': self.show_time.isoformat(), 'price': self.price, 'image_file':self.image_file}



#LOAD USER
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



#FLASK FORMS
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=3, max=8)])
    password = PasswordField('password', validators=[InputRequired()])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=3, max=8)])
    password = PasswordField('password', validators=[InputRequired()])






#INDEX PAGE FOR THE TICKET BOOKING APPLICATION
@app.route('/', methods=['GET', 'POST'])
def index():
    db.create_all()
    return render_template('index.html')


@app.route('/admin/summary', methods=['GET'])
def summary():
    x = []
    y = []
    img=BytesIO()
    Book = Booking.query.all()
    for book in Book:
        show = book.show_id
        shows = Show.query.filter_by(show_id=show)
        for sho in shows:
            x.append(sho.name)
            y.append(book.seats)
    plt.bar(x, y)
    plt.xlabel('shows')
    plt.ylabel('seats')
    plt.title('show_summary')
    plt.savefig(img,format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return render_template('summary.html',plot_url=plot_url)



#REGISTERING USERS
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db.session.add(User(username=form.username.data, password=generate_password_hash(form.password.data, method='sha256')))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)






#USER LOGIN ,DASHBOARD AND PROFILE
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
        user = User.query.filter_by(username = form.username.data)
        if user:
            #print(user)
            for users in user:
                print(users)
                if check_password_hash(users.password, form.password.data):
                    login_user(users,remember=form.remember.data)
                    venues=Venue.query.all()
                    return redirect(url_for('user_dashboard',id=users.id))
        else:
            flash('Invalid Username or password',category='error')
    return render_template('login.html', form=form)

@app.route('/<int:id>/dashboard', methods=['GET', 'POST'])
@login_required
def user_dashboard(id):
    user=User.query.get(id)
    #venue=Venue.query.all()
    venue=Venue.query.all()
    return render_template('dashboard.html',users=user,venues=venue)







#SEARCH FUNCTION
@app.route('/<int:id>/search', methods=['GET', 'POST'])
@login_required
def search(id):
    venue_ser = []
    if request.method == "POST":
        user = User.query.get(id)
        ser = request.form.get('search_query')
        if ser is not None:
            query= "%"+ ser+ "%"
            venue_ser = Venue.query.filter(Venue.location.like(query)).all()
            print(venue_ser )
            show_ser = Show.query.filter(Show.tags.like('%' + ser + '%')).all()
            print(show_ser)
    return render_template('Found.html',result=venue_ser,user=user,results=show_ser)








#BOOKING CREATING AND DISPLAYING
@app.route('/<int:id>/bookings/', methods=['GET', 'POST'])
@login_required
def booking(id):
    if request.method == "GET":
        user= User.query.get(id)
        book=Booking.query.filter_by(user_id=id)
        show=Show.query.all()
    return render_template('Bookings.html',user=user,book=book,shows=show)

@app.route('/show/<int:show_id>/book/<int:id>', methods=['GET', 'POST'])
@login_required
def book(show_id,id):
    if request.method == "GET":
        user = User.query.get(id)
        show= Show.query.get(show_id)
        return render_template('Bookform.html',show=show,user=user)
    elif request.method == "POST":
        user = User.query.get(id)
        show= Show.query.get(show_id)
        user_id=user.id
        show_id = show.show_id
        venue=Venue.query.all()
        seat = request.form['seats']
        con=Booking(user_id=user_id,show_id=show_id,seats=seat)
        db.session.add(con)
        db.session.commit()
    return render_template('dashboard.html',users=user,venues=venue)







#ADMIN LOGIN
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
        user = Admin.query.filter_by(username = form.username.data)
        #print(user)
        if user:
            for users in user:
                if check_password_hash(users.password, form.password.data):
                    login_user(users, remember=form.remember.data)
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Wrong password')
    return render_template('admin_login.html', form=form)

#ADMIN DASHBOARD
@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard(venue_id=None):
    ven= Venue.query.all()
    return render_template('admin_dashboard.html',venues=ven)




#CRUD ON VENUE
#CREATING VENUE
@app.route('/add_venue', methods=['GET', 'POST'])
@login_required
def addvenue():
    if request.method == "GET":
        return render_template("new_venue.html")
    elif request.method == "POST":
        venue_add=VenueAPI()
        venue= venue_add.post()
        return redirect('/admin_dashboard')
    else:
        return redirect('/admin_dashboard')

#UPDATING VENUE
@app.route('/venue/<int:venue_id>/update', methods=["GET", "POST"])
@login_required
def updatevenue(venue_id):
    if request.method == "GET":
        upvenue = Venue.query.get(venue_id)
        return render_template("update_venue.html",upvenue=upvenue )
    elif request.method == "POST":
        venue_edit = VenueAPI()
        venues = venue_edit.put(venue_id)
        return redirect('/admin_dashboard')
    else:
        return redirect('/admin_dashboard')

#DELETING VENUE
@app.route('/venue/<int:venue_id>/delete',methods =["GET","POST"])
@login_required
def deletevenue(venue_id):
    if request.method == "GET":
        venue_delete = VenueAPI()
        VenueDelete=venue_delete.delete(venue_id=venue_id)
        return redirect("/admin_dashboard")
    return redirect("/admin_dashboard")








#CREATING SHOWS
@app.route('/<int:venue_id>/add_show/', methods=['GET', 'POST'])
@login_required
def addshow(venue_id):
    if request.method == "GET":
        venueget=VenueAPI()
        venue=venueget.get(venue_id=venue_id)
        return render_template("new_show.html",venue=venue)
    elif request.method == "POST":
        venue = Venue.query.get(venue_id)
        show_add = ShowAPI()
        show_post = show_add.post(venue_id=venue_id)
        return redirect('/admin_dashboard')
    else:
        return redirect('/admin_dashboard')

#UPDATING SHOWS
@app.route('/show/<int:show_id>/update',methods = ["GET","POST"])
@login_required
def update(show_id):
    if request.method == "GET":
        #upshow = Show.query.get(show_id)
        show_get=ShowAPI()
        upshow=show_get.get(show_id=show_id)
        return render_template("updateshow.html",upshow=upshow)
    if request.method == "POST":
        show_update=ShowAPI()
        show=show_update.put(show_id=show_id)
        return redirect('/admin_dashboard')
    else:
        return redirect('/admin_dashboard')

#DELETING SHOWS
@app.route('/show/<int:show_id>/delete',methods =["GET","POST"])
@login_required
def deleteshow(show_id):
    if request.method == "GET":
        delete_show =ShowAPI()
        deleted = delete_show.delete(show_id=show_id)
        return redirect("/admin_dashboard")
    return redirect("/admin_dashboard")






#LOGOUT FUNCTION FOR BOTH ADMIN AND USER
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)

