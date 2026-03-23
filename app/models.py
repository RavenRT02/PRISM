from flask_login import UserMixin    # provides flask_login req methods like is_authenticated,is_active,is_anonymous,get_id()
                                     # flask_login does not recognise the model as user without UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db,login_manager

class User(UserMixin, db.Model):           # users table

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)

    email = db.Column(db.String(120), unique = True, nullable = False)

    password_hash = db.Column(db.String(255), nullable = False)

    role = db.Column(db.String(20), nullable = False, default = "user")

    is_active = db.Column(db.Boolean, default = True)

    course_end_date = db.Column(db.Date, nullable = True )

    created_at = db.Column(db.DateTime, server_default = db.func.now())

    def set_password(self,password):                         # Convert user pass to hashed pass before storing in db
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):                       # Check if user pass matches hashed pass in db at login
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<user {self.email}>"
    
@login_manager.user_loader                   # Tells flask_login on how to retrieve user from db
def load_user(user_id):
    return User.query.get(int(user_id))


class Building(db.Model):

    __tablename__ = "buildings"

    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(100), nullable = False, unique = True)

    is_active = db.Column(db.Boolean, default = True)


class Floor(db.Model):

    __tablename__ = "floors"

    id = db.Column(db.Integer, primary_key = True)

    number = db.Column(db.String(20), nullable = False)

    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable = False)

    is_active = db.Column(db.Boolean, default = True)

    building = db.relationship("Building", backref = "floors")

    __table_args__ = (db.UniqueConstraint("number", "building_id", name = "uq_floor_building"),)


class Room(db.Model):

    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(50), nullable = False)

    floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable = False)

    is_active = db.Column(db.Boolean, default = True)

    floor = db.relationship("Floor", backref = "rooms")

    __table_args__ = (db.UniqueConstraint("name", "floor_id", name = "uq_room_floor"),)

