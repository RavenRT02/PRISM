from flask_login import UserMixin    # provides flask_login req methods like is_authenticated,is_active,is_anonymous,get_id()
                                     # flask_login does not recognise the model as user without UserMixin
from app.extensions import db,login_manager

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)

    email = db.Column(db.String(120), unique = True, nullable = False)

    password_hash = db.Column(db.String(255), nullable = False)

    role = db.Column(db.String(20), nullable = False, default = "user")

    is_active = db.Column(db.Boolean, default = True)

    created_at = db.Column(db.DateTime, server_default = db.func.now())


    def __repr__(self):
        return f"<user {self.email}>"
    
@login_manager.user_loader                   # Tells flask_login on how to retrieve user from db
def load_user(user_id):
    return User.query.get(int(user_id))