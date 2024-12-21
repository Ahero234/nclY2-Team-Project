import bcrypt
from datetime import datetime, timedelta
import itsdangerous
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app as app
from extensions import db, mdb
from flask_login import UserMixin
import pyotp


"""
All user (including admin) accounts

"""
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    height = db.Column(db.Float(5), nullable=False)
    role = db.Column(db.String(15), nullable=False)
    dob = db.Column(db.String(15), nullable=False)
    created = db.Column(db.DateTime, nullable=False)
    last_change_username = db.Column(db.DateTime, nullable=True)
    pin_key = db.Column(db.String(32), nullable=False, default=pyotp.random_base32())
    diary_entries = db.relationship("DiaryEntry", backref="user", cascade="all, delete-orphan", lazy=True)
    change_username_logs = db.relationship("ChangeUsernameLog", backref="user", lazy=True, cascade="all, "
                                                                                                   "delete-orphan")
    recipe_ratings = db.relationship("RecipeRating", backref="user", cascade="all, delete-orphan", lazy=True)
    bookmarks = db.relationship("Bookmark", backref="user", lazy=True, cascade="all, delete-orphan")
    medicines = db.relationship("Medicine", backref="user", lazy=True, cascade="all, delete-orphan")


    def __init__(self, email, username, password, height, first_name, last_name, role, dob):
        self.email = email
        self.username = username
        self.password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self.first_name = first_name
        self.last_name = last_name
        self.height = height
        self.role = role
        self.dob = dob
        self.created = datetime.now()
        self.pin_key = pyotp.random_base32()


    # Check if the input password matches the stored password after encoding
    def validate_password(self, password):
        test = bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))
        print("Password test: " + str(test))
        return test


    def verify_pin(self, pin):
        return pyotp.TOTP(self.pin_key).verify(pin)


    def get_2fa_uri(self):
        return str(pyotp.totp.TOTP(self.pin_key).provisioning_uri(name=self.email, issuer_name="Group 4 - 4health"))


    # Creating a TOTP object using the pin_key and verifying the OTP
    def validate_otp(self, otp):
        test = pyotp.TOTP(self.pin_key).verify(otp)
        print("otp test: " + str(test))
        return test


    # Code found from here: https://freelancefootprints.substack.com/p/yet-another-password-reset-tutorial
    def get_reset_token(self):
        s = Serializer(app.config["SECRET_KEY"])
        return s.dumps(self.email, salt=self.password)


    # Retrieve the user from the database using the provided user_id
    @staticmethod
    def validate_reset_password_token(token: str, user_id: int):
        user = db.session.get(User, user_id)
        # Check if the user exists
        # print(user.email)
        if user is None:
            return None
        s = Serializer(app.config["SECRET_KEY"])
        try:
            token_user_email = s.loads(token, max_age=int(app.config["RESET_PASS_TOKEN_MAX_AGE"]),
                                       salt=user.password)
        except(itsdangerous.SignatureExpired, itsdangerous.BadSignature):
            return None

        if token_user_email != user.email:
            return None
        print(user.email)
        return user


    def can_change_username(self):
        return self.last_change_username is None or (datetime.now() - self.last_change_username) > timedelta(minutes=10)


    def change_username(self, new_username):
        if not self.can_change_username():
            raise ValueError("USERNAME CAN BE CHANGED EVERY 10 MINUTE YOU WILL BE ABLE TO CHANGE IT AGAIN ON " + str(
                self.last_change_username + timedelta(minutes=10)))
        old_username = self.username
        self.username = new_username
        self.last_change_username = datetime.now()
        username_change_log = ChangeUsernameLog(self.id, old_username, new_username)
        db.session.add(username_change_log)

        for recipe in get_recipes():  # iterate through all recipes
            if recipe["created_by"] == old_username:  # if recipe was created by this user
                update_mdb_value(recipe["id"], "created_by", new_username)  # change old username to new username

        db.session.commit()


"""
Recipes are stored in a separate Mongo database, and its functionality is defined below

"""
 # Define the collection name for the recipes
recipes = mdb["recipes"]["recipes"]


# WARNING: ALL EXISTING RECIPES WILL BE REMOVED FROM THE DATABASE WITH THIS FUNCTION
def reset_recipes():
    print("[DEBUG] DELETING ALL RECIPES")
    return recipes.delete_many({})  # remove every document from the collection


# add a new recipe to the database, by default with state "unapproved"
def add_recipe(created_by, title, category, tags, summary, ingredients, instructions, preparation_time,
               servings, calories_per_serving, private=False):
    current_time = datetime.now()
    state = "unapproved"
    highest_recipe_id = 1
    for recipe in get_recipes():
        if recipe["id"] > highest_recipe_id:
            highest_recipe_id = recipe["id"]
    recipe_id = highest_recipe_id + 1  # determines id of next recipe

    recipe_doc = {"id": recipe_id, "title": title, "created_by": created_by, "created_at": current_time,
                  "category": category, "tags": tags, "summary": summary, "ingredients": ingredients,
                  "instructions": instructions, "preparation_time": preparation_time, "servings": servings,
                  "calories_per_serving": calories_per_serving, "state": state, "private": private}
    result = recipes.insert_one(recipe_doc)  # adds to database
    print("Added recipe. Result: " + str(result))
    return recipe_doc


# return all recipes (optionally including filters)
def get_recipes(filters={}):
    return recipes.find(filters)


# return the recipe with the matching ID
def get_recipe(recipe_id):
    return recipes.find_one({"id": recipe_id})


# check whether there are any approved recipes
def approved_recipes_exist():
    if recipes.count_documents({"state": "approved"}) > 0:
        return True  # there is at least one approved recipe in the database
    return False  # there are no approved recipes


# check whether there are any unapproved recipes
def unapproved_recipes_exist():
    if recipes.count_documents({"state": "unapproved"}) > 0:
        return True  # there is at least one unapproved recipe in the database
    return False  # there are no unapproved recipes


# change the value for a recipe's property (key)
def update_mdb_value(target_id, key, value):
    return mdb["recipes"]["recipes"].update_one({"id": target_id}, {"$set": {key: value}}, upsert=False)


# remove recipe from database
def mdb_delete_recipe(recipe_id):
    return recipes.delete_one({"id": recipe_id})


# remove recipe from database
def mdb_approve_recipe(recipe_id):
    update_mdb_value(recipe_id, "state", "approved")


# DEBUG function used to set all states of recipes to approved
def mdb_set_states():
    print("Setting all recipe states to approved")
    recipes_list = get_recipes()
    for recipe in recipes_list:
        update_mdb_value(recipe["id"], "state", "approved")

    print("Update complete")


# DEBUG function used to migrate the original raw strings of properties like ingredients (now lists of strings)
def mdb_split_lines():
    print("Updating mdb with line splitting")
    recipes_list = get_recipes()
    keys = ["tags", "ingredients", "instructions"]
    for recipe in recipes_list:
        print("- Recipe: " + str(recipe["title"]))
        for key in keys:
            print("-  - Key: " + key)
            current_value = recipe[key]
            if key == "tags":
                new_value = current_value.split(", ")
            else:
                new_value = current_value.split("\r\n")
            print("-  -  - CURRENT VALUE: " + str(current_value))
            print("-  -  - NEW VALUE: " + str(new_value))
            update = update_mdb_value(recipe["id"], key, new_value)
            print(update)

    print("Update complete")


"""
Relational table to provide a rating (and optionally review) to a specific recipe, by a specific user
"""
class RecipeRating(db.Model):
    __tablename__ = "recipe_ratings"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, nullable=False) # Mongo foreign key
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(1000), nullable=True)
    rated_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, recipe_id, user_id, value, review=None):
        self.recipe_id = recipe_id
        self.user_id = user_id
        self.value = value
        self.review = review
        self.rated_at = datetime.now()

    def update_value(self, value):
        self.value = value


"""
Relational table to represent a recipe being saved in a user's bookmarks
"""
class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, nullable=False) # Mongo foreign key
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    bookmarked_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, recipe_id, user_id):
        self.recipe_id = recipe_id
        self.user_id = user_id
        self.bookmarked_at = datetime.now()


"""
A user's log of various health-related activities and stats during a specific day
"""
class DiaryEntry(db.Model):
    __tablename__ = "diary_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    calorie_intake = db.Column(db.Integer, nullable=False)
    calorie_burned = db.Column(db.Integer, nullable=False)
    steps = db.Column(db.Integer, nullable=False)
    hours_of_sleep = db.Column(db.Integer, nullable=False)
    diary_log = db.Column(db.String(200), nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "date", name="unique_user_date"),)

    def __init__(self, user_id, date, weight, height, calorie_intake, calorie_burned, steps, hours_of_sleep, diary_log):
        self.user_id = user_id
        self.date = date
        self.weight = weight
        self.bmi = weight / ((height / 100) ** 2)
        self.calorie_intake = calorie_intake
        self.calorie_burned = calorie_burned
        self.steps = steps
        self.hours_of_sleep = hours_of_sleep
        self.diary_log = diary_log

    def __repr__(self):
        return f"Diary Entry('{self.date}', '{self.weight}', '{self.bmi}', '{self.calorie_intake}', '{self.calorie_burned}', '{self.steps}', '{self.hours_of_sleep}', '{self.diary_log}')"



"""
A log of usernames being changed
"""
class ChangeUsernameLog(db.Model):
    __tablename__ = "change_username_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    old_username = db.Column(db.String(100), nullable=False)
    new_username = db.Column(db.String(100), nullable=False)
    change_time = db.Column(db.DateTime, nullable=False)

    def __init__(self, user_id, old_username, new_username):
        self.user_id = user_id
        self.old_username = old_username
        self.new_username = new_username
        self.change_time = datetime.now()


"""
This table lists medicine that a user has saved, with a separate table for doses
"""
class Medicine(db.Model):
    __tablename__ = "medicines"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(50))
    doses = db.relationship("Dose", backref="Medicine", cascade="all, delete-orphan", lazy=True)

    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name


"""
This table lists the doses belonging to a particular medicine
"""
class Dose(db.Model):
    __tablename__ = "doses"
    id = db.Column(db.Integer, primary_key=True)
    med_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)
    dose = db.Column(db.String(50), nullable=False)
    time = db.Column(db.Time, nullable=False)

    def __int__(self, med_id, dose, time):
        self.med_id = med_id
        self.dose = dose
        self.time = time


# initialize database
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
