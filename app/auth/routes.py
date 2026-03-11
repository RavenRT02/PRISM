from flask import Blueprint, request
from flask_login import login_user, logout_user, login_required
from app.models import User

auth_bp = Blueprint("auth", __name__)  # Blueprint(name_of_blueprint, location_of_files)

@auth_bp.route("/login", methods = ["GET","POST"])
def login():
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email = email).first()

        if user and user.check_password(password):
            login_user(user)
            return "Login Successful"
        
        return "Invalid Credentials"
    
    return "Login Page"

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return "Logged Out"
