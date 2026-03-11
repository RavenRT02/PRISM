from app.extensions import db

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)

    email = db.Column(db.String(120), unique = True, nullable = False)

    role = db.Column(db.String(20), nullable = False, default = "user")

    is_active = db.Column(db.Boolean, default = True)

    created_at = db.Column(db.DateTime, server_default = db.func.now())


    def __repr__(self):
        return f"<user {self.email}>"