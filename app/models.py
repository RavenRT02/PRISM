from flask_login import UserMixin    # provides flask_login req methods like is_authenticated,is_active,is_anonymous,get_id()
                                     # flask_login does not recognise the model as user without UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db,login_manager

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)

    email = db.Column(db.String(120), unique = True, nullable = False)

    password_hash = db.Column(db.String(255), nullable = False)

    role = db.Column(db.String(20), nullable = False, default = "user")

    is_active = db.Column(db.Boolean, default = True)

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