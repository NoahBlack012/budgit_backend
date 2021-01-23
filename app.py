#Get rid of uuid for item
from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS
import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
import os
import bcrypt
import json
import random
import datetime
#venv\Scripts\activate
#$env:FLASK_APP='app.py'

app = Flask(__name__)
CORS(app)
DATABASE_URI = os.environ["DATABASE_URI"]
API_KEY = os.environ["API_KEY"]
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    categories = db.Column(db.ARRAY(db.String), nullable=False, default=["Food", "Transportation", "Shopping", "Rent"])

    def __repr__(self):
        return f"User('{self.username}', '{self.password}', '{self.id}', '{self.categories}')"

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)
    value = db.Column(db.Numeric, nullable=False)
    category = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=f"{datetime.datetime.now().year}-{datetime.datetime.now().month}-{datetime.datetime.now().day}")

    def __repr__(self):
        return f"Item('{self.id}', '{self.userid}', '{self.title}', '{self.value}', '{self.category}')"

def check_api_key(sent_key):
    if sent_key == API_KEY:
        return True
    else:
        return False

@app.route("/api/signup", methods=["POST"])
def signup():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    db_users = User.query.filter_by(username=username)
    for user in db_users:
        if user.username == username:
            return jsonify({"user_created": False})

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(username=username, password=hashed_password.decode('utf-8'))
    db.session.add(new_user)
    db.session.commit()
    userid = new_user.id #User.query.filter_by(username=username).first().id
    return jsonify({"user_created": True, "userid": userid})

@app.route("/api/login", methods=["POST"])
def login():
    sent_key = request.json.get("api_key", None)
    if not check_api_key(sent_key):
        return jsonify({"status_code": 401})
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    db_user = User.query.filter_by(username=username).first()

    #If the username is not in the db
    if not db_user:
        return jsonify({"status_code": 200, "login": False})
        
    db_password = db_user.password
    if bcrypt.checkpw(password.encode('utf-8'), db_password.encode('utf-8')):
        return jsonify({"status_code": 200, "userid": db_user.id, "login": True})
    else:
        return jsonify({"status_code": 200, "login": False})

@app.route("/api/get_items", methods=["POST"])#@login_required
def get_items():
    userid = request.json.get("userid", None)
    sent_key = request.json.get("api_key", None)
    if not check_api_key(sent_key):
        return make_response(jsonify({"status_code": 401}), 401)
    items = Item.query.filter_by(userid=userid).all()
    json_items = []
    for item in items:
        json_items.append(
            {
                "id": item.id,
                "userid": item.userid,
                "title": item.title,
                "value": float(item.value),
                "category": item.category, 
                "date": str(item.date)
            }
        )
    res = make_response(jsonify({"status_code": 200, "items": json_items}), 200)
    return res

@app.route("/api/add_item", methods=["POST"])
def add_item():
    userid = request.json.get("userid", None)
    sent_key = request.json.get("api_key", None)
    new_item = request.json.get("new_item", None)
    if not check_api_key(sent_key):
        return make_response(jsonify({"status_code": 401}), 401)

    #item = Item(userid=1, title="ABC", value=123, category="food")
    new_item_object = Item(
        userid=userid,
        title=new_item["title"],
        value=new_item["value"],
        category=new_item["category"], 
    )
    db.session.add(new_item_object)
    db.session.commit()
    return make_response(jsonify({"status_code": 200, "id": new_item_object.id}), 200)

@app.route("/api/delete_item", methods=["POST"])
def delete_item():
    userid = request.json.get("userid", None)
    sent_key = request.json.get("api_key", None)
    deleted_id = request.json.get("deleted_id", None)
    if not check_api_key(sent_key):
        return make_response(jsonify({"status_code": 401}), 401)

    if Item.query.filter_by(id=deleted_id).first().userid == userid:
        Item.query.filter_by(id=deleted_id).delete() #delete the item with the id provided from the db
    else:
        return make_response(jsonify({"status_code": 401}), 401)
        
    db.session.commit()
    return make_response(jsonify({"status_code": 200}), 200)

@app.route("/api/add_category", methods=["POST"])
def add_category():
    userid = request.json.get("userid", None)
    sent_key = request.json.get("api_key", None)
    new_category = request.json.get("new_category", None)
    if not check_api_key(sent_key):
        return make_response(jsonify({"status_code": 401}), 401)
    categories = User.query.filter_by(id=userid).first().categories
    categories.append(new_category)
    User.query.filter_by(id=userid).first().categories = categories
    db.session.commit()
    user_categories = User.query.filter_by(id=userid).first().categories
    return make_response(jsonify({"status_code": 200, "categories": user_categories}), 200)

@app.route("/api/get_categories", methods=["POST"])
def get_categories():
    userid = request.json.get("userid", None)
    sent_key = request.json.get("api_key", None)
    if not check_api_key(sent_key):
        return make_response(jsonify({"status_code": 401}), 401)
    user_categories = User.query.filter_by(id=userid).first().categories
    return make_response(jsonify({"status_code": 200, "categories": user_categories}), 200)

@app.route("/api/get_pie_totals", methods=["POST"])
def get_pie_totals():
    userid = request.json.get("userid", None)
    sent_key = request.json.get("api_key", None)
    if not check_api_key(sent_key) or not userid:
        return make_response(jsonify({"status_code": 401}), 401)
    user_categories = User.query.filter_by(id=userid).first().categories
    user_items = Item.query.filter_by(userid=userid).all()

    category_datasets = []
    category_totals = []
    backgroundcolors = []
    for category in user_categories:
        category_totals.append(0)
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        backgroundcolors.append(f"rgba({r}, {g}, {b}, 1")
    for item in user_items:
        for category in user_categories:
            if item.category == category:
                category_totals[user_categories.index(category)] += float(item.value)

    category_obj = {
        "labels": [category for category in user_categories],
        "datasets": [
            {
                "label": "Total",
                "data": category_totals,
                "backgroundColor": [color for color in backgroundcolors]
            }
        ]
    }

    return make_response(jsonify({"status_code": 200, "totals_datasets": category_obj}), 200)

@app.route("/api/get_monthly_bar_totals", methods=["POST"])
def get_monthly_bar_totals():
    userid = request.json.get("userid", None)
    sent_key = request.json.get("api_key", None)
    if not check_api_key(sent_key):
        return make_response(jsonify({"status_code": 401}), 401)
    user_items = Item.query.filter_by(userid=userid).all()

    months = []
    for item in user_items:
        months.append(item.date.month)

    data = []
    for month in range(1, 13):
        items = [item for item in user_items if item.date.month == month and item.date.year == datetime.datetime.now().year]
        items_sum = 0
        for item in items:
            items_sum += int(item.value)
        data.append(items_sum)

    label_months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    bar_data = {
        "labels": label_months, 
        "datasets": [
            {
                "label": "Monthy Expendatures",
                "backgroundColor": 'rgba(92, 207, 92, 1)', 
                "data": data, 
            }
        ]
    }

    return make_response(jsonify({"status_code": 200, "bar_data": bar_data}), 200)

if __name__ == '__name__':
    app.run(debug=True)
