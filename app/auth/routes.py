from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.utils.email import send_otp_email

auth_bp = Blueprint("auth", __name__)  # Blueprint(name_of_blueprint, location_of_files)

@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods = ["GET","POST"])
def login():
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email = email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("auth.dashboard"))
        
        return render_template("login.html", error = "Invalid Credentials")
    
    return render_template("login.html")

@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

