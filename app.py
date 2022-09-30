from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_bcrypt import Bcrypt
# import os


app = Flask(__name__)
CORS(app)


# basedir = os.path.abspath(os.path.dirname(__file__))
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + \
#     os.path.join(basedir, "app.sqlite")

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://kghacauwujxcsc:9322b1ce9e5bc9fd5450d0de6adf3b52518cdbe659bd9794a6aac164251f60a9@ec2-34-230-153-41.compute-1.amazonaws.com:5432/d58vhoeg3oq663"


db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    email = db.Column(db.String(320), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    db_logged_in = db.Column(db.String)

    def __init__(self, email, password, db_logged_in):
        self.email = email
        self.password = password
        self.db_logged_in = db_logged_in


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    rating = db.Column(db.String, nullable=True)
    value = db.Column(db.Integer, nullable=True)

    def __init__(self, rating, value):
        self.rating = rating
        self.value = value


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, title, user_id):
        self.title = title
        self.user_id = user_id


class ActivityRating(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey(
        'activity.id'), nullable=False)
    rating_id = db.Column(db.Integer, db.ForeignKey(
        'rating.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, activity_id, rating_id, user_id):
        self.activity_id = activity_id
        self.rating_id = rating_id
        self.user_id = user_id


class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "email", "password", "db_logged_in")


user_schema = UserSchema()
multi_user_schema = UserSchema(many=True)


class RatingSchema(ma.Schema):
    class Meta:
        fields = ("id", "rating", "value")


rating_schema = RatingSchema()
multi_rating_schema = RatingSchema(many=True)


class ActivitySchema(ma.Schema):
    class Meta:
        fields = ("id", "title", "user_id")


activity_schema = ActivitySchema()
multi_activity_schema = ActivitySchema(many=True)


class ActivityRatingSchema(ma.Schema):
    class Meta:
        fields = ("id", "activity_id", "rating_id", "user_id")


activity_rating_schema = ActivityRatingSchema()
multi_activity_rating_schema = ActivityRatingSchema(many=True)


@app.route('/activityrating/add', methods=['POST'])
def add_activity_rating():
    post_data = request.get_json()
    activity_id = post_data.get('activity_id')
    rating_id = post_data.get('rating_id')
    user_id = post_data.get('user_id')

    new_activity_rating = ActivityRating(activity_id, rating_id, user_id)
    db.session.add(new_activity_rating)
    db.session.commit()

    return jsonify('activity has been rated')


@app.route("/user/add", methods=['POST'])           # ADD ONE USER
def add_user():
    post_data = request.get_json()
    email = post_data.get('email')
    password = post_data.get('password')
    db_logged_in = post_data.get('db_logged_in')
    possible_dup = db.session.query(User).filter(
        User.email == email).first()

    if possible_dup is not None:
        return jsonify('Error: that email already exists.')

    encrypted_password = bcrypt.generate_password_hash(
        password).decode('utf-8')
    new_user = User(email, encrypted_password, db_logged_in)
    db.session.add(new_user)
    db.session.commit()

    return jsonify('you have created a new user, Welcome to the site.')


@app.route("/activity/add", methods={'POST'})           # ADD ONE ACTIVITY
def add_activity():
    post_data = request.get_json()
    title = post_data.get('title')
    user_id = post_data.get('user_id')
    possible_dup = db.session.query(Activity).filter(
        Activity.title == title).first()

    if possible_dup is not None:
        return jsonify('Error: that Activity already exists.')

    new_activity = Activity(title, user_id)
    db.session.add(new_activity)
    db.session.commit()

    return jsonify(activity_schema.dump(new_activity))


@app.route('/user/add/many', methods=['POST'])          # ADD MANY USERS
def add_many_users():
    if request.content_type != 'application/json':
        return jsonify("Error try again this time with JSON Simpleton!")

    post_data = request.get_json()
    users = post_data.get('users')
    new_records = []

    for user in users:
        email = user.get('email')
        password = user.get('password')
        db_logged_in = "NOT_LOGGED_IN"

        possible_dup = db.session.query(User).filter(
            User.email == email).first()

        if possible_dup is not None:
            return jsonify('Error: that email already exists.')
        else:
            encrypted_password = bcrypt.generate_password_hash(
                password).decode('utf-8')
            new_record = User(email, encrypted_password, db_logged_in)
            db.session.add(new_record)
            db.session.commit()
            new_records.append(new_record)

    return jsonify(multi_user_schema.dump(new_records))


@app.route("/rating/get", methods={'GET'})          # GET ALL RATINGS
def get_all_ratings():
    all_ratings = db.session.query(Rating.rating)
    return jsonify(multi_rating_schema.dump(all_ratings))


@app.route("/activity/get", methods={'GET'})            # GET ALL ACTIVITIES
def get_all_activities():
    all_records = db.session.query(Activity).all()
    return jsonify(multi_activity_schema.dump(all_records))


@app.route('/user/get/<id>', methods=['GET'])           # GET USER BY ID
def get_user(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))


@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(multi_user_schema.dump(all_users))


# ---------------- handleSubmit -----------------
@app.route("/user/verification", methods=["POST"])
def verification():
    if request.content_type != "application/json":
        return jsonify("ERROR: Check your headers!")

    post_data = request.get_json()
    email = post_data.get("email")
    password = post_data.get("password")

    user = db.session.query(User).filter(User.email == email).first()
    id = user.id

    if user is None:
        return jsonify("User could not be Verfied!")

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify("User could not be Verfied!")

    return jsonify(id)


@app.route("/login/<id>", methods=["PUT"])          # LOGIN BY ID
def loginUser(id):
    if request.content_type != "application/json":
        return jsonify("ERROR: Check your headers!")

    user = db.session.query(User).filter(User.id == id).first()
    user.db_logged_in = "LOGGED_IN"
    db.session.commit()

    return jsonify('you have logged in on the db')


@app.route("/logout/<id>", methods=["PUT"])         # LOG OUT
def logoutUser(id):
    if request.content_type != "application/json":
        return jsonify("ERROR: Check your headers!")

    user = db.session.query(User).filter(User.id == id).first()
    user.db_logged_in = "NOT_LOGGED_IN"
    db.session.commit()

    return jsonify('you have logged off of the db')


@app.route("/rating/add/many", methods=['POST'])            # ADD MANY RATINGS
def add_rating():
    if request.content_type != 'application/json':
        return jsonify("Error try again this time with JSON Simpleton!")

    post_data = request.get_json()
    ratings = post_data.get("ratings")
    new_records = []

    for r in ratings:
        rating = r.get('rating')
        value = r.get('value')

        existing_rating_check = db.session.query(
            Rating).filter(Rating.rating == rating).first()
        if existing_rating_check is not None:
            return jsonify("Rating already exists!")
        else:
            new_record = Rating(rating, value)
            db.session.add(new_record)
            db.session.commit()
            new_records.append(new_record)

    return jsonify('You have created new Ratings')


# DELETE ACTIVITY BY ID
@app.route('/activity/delete/<id>', methods=['DELETE'])
def delete_activity(id):
    delete_activity = db.session.query(
        Activity).filter(Activity.id == id).first()
    db.session.delete(delete_activity)
    db.session.commit()

    return jsonify(activity_schema.dump(delete_activity), "Activity was successfully deleted")


if __name__ == "__main__":
    app.run(debug=True)
