"""Coffee_buddy"""
import os
from jinja2 import StrictUndefined
from flask import Flask, render_template, redirect, request, flash, session, url_for
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.utils import secure_filename
from models import *
from queries import *
from matchmaker import *

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/user_profile_pictures'
# Flask sessions and the debug toolbar
app.secret_key = "ABC"

# this will throw an error if a jinja variable is undefined
app.jinja_env.undefined = StrictUndefined


###################################################################################################################

@app.route('/')
def index():
    """Homepage."""
    return render_template('homepage.html')

@app.route('/login', methods=["GET"])
def login_input():
    """For user to login with email"""

    return render_template('login.html')


@app.route('/login', methods=["POST"])
def check_login():
    """Check user login info"""
    
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter(User.email == email).first()

    if not user:
        flash('Please register your account')
        return redirect('/register')
    elif email == user.email and password == user.password:
        session['user_id'] = user.user_id
        flash('You successfully logged in')
        return redirect('/plan_trip')


@app.route('/register', methods=["GET"])
def register_form():
    """For user to register with email"""

    all_interests = [all_book_genres(), all_movie_genres(),
                     all_music_genres(), all_food_habits(),
                     all_fav_cuisines(), all_hobbies(),
                     all_political_views(), all_religions(),
                     all_outdoors()]

    return render_template('register.html',
                                all_interests=all_interests)


@app.route('/register', methods=["POST"])
def register_process():
    """Get user registration and redirect to user_interests"""

    fname = request.form.get('fname').capitalize()
    lname = request.form.get('lname').capitalize()
    email = request.form.get('email')
    user_name = request.form.get('user_name')
    password = request.form.get('password')
    date_of_birth = request.form.get('date_of_birth')
    zipcode = request.form.get('zipcode')
    phone = request.form.get('phone')
    one_word = request.form.get('one_word')
    book_genre_id = request.form.get('Preferred book genre')
    movie_genre_id = request.form.get('Preferred movie genre')
    music_genre_id = request.form.get('Preferred music genre')
    food_habit_id = request.form.get('Food habits')
    fav_cuisine_id = request.form.get('Preferred cuisine type')
    hobby_id = request.form.get('Favorite hobby')
    political_view_id = request.form.get('Political ideology')
    religion_id = request.form.get('Religious ideology')
    file = request.files.get('profile_picture', None)
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    profile_picture = 'static/user_profile_pictures/' + str(filename)
    outdoor_id = request.form.get('Favorite Outdoor activity')



    user = db.session.query(User).filter(User.email == email).first()

    if not user:
        # if the user does not exist then we instantiate a user and the info
        #to the db
        user = User(fname=fname,
                    lname=lname,
                    email=email, 
                    user_name=user_name,
                    password=password,
                    date_of_birth=date_of_birth,
                    zipcode=zipcode,
                    phone=phone,
                    one_word=one_word,
                    profile_picture=profile_picture)


        db.session.add(user)
        db.session.commit()
        userid = user.user_id

        #update user interests for the specific user
        interest = Interest(
                    user_id=userid,
                    book_genre_id=book_genre_id,
                    movie_genre_id=movie_genre_id, 
                    music_genre_id=music_genre_id,
                    food_habit_id=food_habit_id,
                    fav_cuisine_id=fav_cuisine_id,
                    hobby_id=hobby_id,
                    political_view_id=political_view_id,
                    religion_id=religion_id,
                    outdoor_id=outdoor_id
                    )

        db.session.add(interest)
        db.session.commit()

    session['user_id'] = user.user_id
    flash('You are successfully registerd and logged in')
    return redirect('/plan_trip')
    

@app.route('/user_info', methods=["GET"])
def show_profile():
    """show the user their own profile"""

    userid = session.get("user_id")

    user_info = get_user_info(userid)

    return render_template('/user_info.html',user_info=user_info)


@app.route('/plan_trip', methods=["GET"])
def show_map():
    """Show a map with coffeeshops
    Putting in time constraints for the user input via 
    HTML so that every input is a valid input """


    return render_template("/plan_trip.html")


@app.route('/plan_trip', methods=["POST"])
def plan_trip():
    """get trip time, pincode"""

    query_time = request.form.get('triptime')
    query_pin_code = request.form.get('pincode')
    user_id = session['user_id']
    session['query_pincode'] = query_pin_code

    #add user query to the db

    trip =  PendingMatch(
                    user_id=user_id,
                    query_pin_code=query_pin_code,
                    query_time=query_time,
                    pending=True
                    )

    db.session.add(trip)
    db.session.commit()

    #at this point we will pass the information the yelper
    #yelper will end information to google and google will render
    # a map with relevant information
    
    return redirect("/show_matches")

@app.route('/show_matches',methods=['GET'])
def show_potenital_matches():
    """show a logged in user possible matches"""

    userid = session.get('user_id')
    pin = session.get('query_pincode')


    potential_matches = query_pending_match(pin)
    #this is a list of user_ids
    #[189, 181, 345, 282, 353, 271, 9, 9, 501, 9]
    match_percents = create_matches(potential_matches, userid)
    #this is a list of tuples 
    """create_matches([30,40,50],60)
    => [(60, 30, 57.90407177363699), (60, 40, 54.887163561076605)
    ,(60, 50, 71.24706694271913)]
    """
    user_info = get_user_info(userid)
    # this is the logged in user's info
    user_name = get_user_name(userid)
    # this is the logged in user's username

    match_info = []

    for user in match_percents:
        username = get_user_name(user[1])
        matched_username = username[0] + " " + username[1]
        match_percent = round(user[2])

        match_info.append((matched_username, match_percent))

    #match info is a list of tuples [(username, match_percent)]
    return render_template('show_matches.html',
                                user_name=user_name, 
                                user_info=user_info,
                                match_info=match_info)

@app.route('/show_map', methods=["GET"])
def choose_coffee_shop():
    """get user query"""
    

    return render_template('map.html')



###################################################################################################################


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')