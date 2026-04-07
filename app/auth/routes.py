from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, UserOTP
from app.utils.otp import create_otp, can_resend_otp, verify_otp_code
from app.utils.datetime_utils import ensure_utc
from app.utils.email import send_otp_email
from app.utils.password import validate_password_strength
from app.utils.captcha import generate_captcha
from datetime import datetime, timezone, timedelta, date


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

        if not user:
            flash("Invalid credentials", "error")
            return redirect(url_for("auth.login"))
        
        if not user.is_password_set:
            flash("Please set your password first", "error")
            return redirect(url_for("auth.set_password_start"))

        if not user.check_password(password):
            flash("Invalid Credentials", "error")
            return redirect(url_for("auth.login"))
        
        if not user.is_active:

            flash("Your account has been disabled. Contact administrator.", "error")
            return redirect(url_for("auth.login"))

        if user.course_end_date is not None and user.course_end_date < date.today():   # admin and staff have NULL (None) date

            user.is_active = False
            db.session.commit()

            flash("Your course access has expired.", "error")
            return redirect(url_for("auth.login"))
        
        login_user(user)
        if current_user.role == "admin":

            return redirect(url_for("dashboard.admin_dashboard"))

        return redirect(url_for("dashboard.user_dashboard"))
    
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/set-password-start", methods = ['GET', 'POST'])
def set_password_start():

    if request.method == 'POST':

        email = request.form.get("email")
        user = User.query.filter_by(email = email).first()

        if not user:
            flash("Email not found", "error")
            return(redirect(url_for("auth.set_password_start")))
        
        if user.is_password_set:
            flash("Password already set, use reset password instead", "warning")
            return(redirect(url_for("auth.login")))
        
        if not can_resend_otp(user, "FIRST_LOGIN"):
            flash("Please wait before requesting a new OTP", "warning")
            return redirect(url_for("auth.set_password_start"))
        
        otp = create_otp(user, "FIRST_LOGIN")

        send_otp_email(user.email, otp, "FIRST_LOGIN")

        session["otp_user_email"] = email               # prevents parameter tampering in url, secure server-side memory stored per user browser
        session["otp_verified"] = False                 # prevents user from skipping otp verification from altering url 
        
        flash("OTP sent to your registered email", "success")

        return(redirect(url_for("auth.verify_otp")))
    
    return render_template("set_password_start.html")


@auth_bp.route("/verify-otp", methods = ['GET', 'POST'])
def verify_otp():

    email = session.get("otp_user_email")

    if not email:
        flash("Session expired", "error")
        return redirect(url_for("auth.set_password_start"))
    
    user = User.query.filter_by(email = email).first()

    if not user:
        flash("Invalid request", "error")
        return redirect(url_for("auth.login"))
    
    if request.method == 'POST':

        entered_otp = request.form.get("otp")
        entered_captcha = request.form.get("captcha")
        stored_captcha = session.get("captcha_text")

        if not stored_captcha or entered_captcha != stored_captcha:
            flash("Invalid captcha", "error")
            return redirect(url_for("auth.verify_otp"))
        session.pop("captcha_text", None)

        success, message = verify_otp_code(user, entered_otp, "FIRST_LOGIN")

        if not success:
            flash(message, "error")
            return redirect(url_for("auth.verify_otp"))  

        session["otp_verified"] = True 
        session["otp_verified_at"] = datetime.now(timezone.utc).isoformat()
        flash("OTP verified sucessfully", "success")

        return redirect(url_for("auth.set_password"))
    
    latest_otp = UserOTP.query.filter_by(user_id = user.id,
                                         purpose = "FIRST_LOGIN", is_used = False).order_by(UserOTP.created_at.desc()).first()
    remaining_seconds = 0

    if latest_otp:
        cooldown_end = latest_otp.created_at + timedelta(minutes=2)
        cooldown_end = ensure_utc(cooldown_end)
        remaining_seconds = max(0, int((cooldown_end - datetime.now(timezone.utc)).total_seconds()))
    
    captcha_text = generate_captcha()
    session["captcha_text"] = captcha_text

    return render_template("verify_otp.html", remaining_seconds = remaining_seconds, captcha_text = captcha_text)


@auth_bp.route("/set-password", methods = ['GET', 'POST'])
def set_password():

    email = session.get("otp_user_email")
    verified = session.get("otp_verified")
    verified_at_str = session.get("otp_verified_at")

    if not email or not verified:
        flash("Session expired. Please restart verification", "error")
        return redirect(url_for("auth.set_password_start"))
    
    if not verified_at_str:
        flash("Verification expired. Request a new OTP", "error")
        return redirect(url_for("auth.set_password_start"))
    
    verified_at = datetime.fromisoformat(verified_at_str)
    verified_at = ensure_utc(verified_at)

    if datetime.now(timezone.utc) - verified_at > timedelta(minutes=5):
        flash("Verification expired, Request a new OTP", "error")
        return redirect(url_for("auth.set_password_start"))

    user = User.query.filter_by(email = email).first()

    if not user:
        flash("Invalid request", "error")
        return redirect(url_for("auth.login"))
    
    if request.method == 'POST':

        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.set_password"))
        
        valid, message = validate_password_strength(password)

        if not valid:
            for msg in message:
                flash(msg, "error")
            return redirect(url_for("auth.set_password"))
        
        user.set_password(password)
        user.is_password_set = True

        UserOTP.query.filter_by(user_id = user.id, purpose = "FIRST_LOGIN", 
                                is_used = False).update({"is_used" : True}) # Invalidates all existing OTP (handled in create_otp , additional safety)
        
        db.session.commit()

        session.pop("otp_user_email", None)
        session.pop("otp_verified", None)
        session.pop("otp_verified_at", None)

        flash("Password set successfully please login", "success")

        return redirect(url_for("auth.login"))
    
    return render_template("set_password.html")


@auth_bp.route("/resend-otp")
def resend_otp():

    email = session.get("otp_user_email")

    if not email:
        flash("Session expired, Please restart verification", "error")
        return redirect(url_for("auth.set_password_start"))
    
    user = User.query.filter_by(email = email).first()

    if not user:
        flash("Invalid user", "error")
        return redirect(url_for("auth.login"))
    
    if not can_resend_otp(user, "FIRST_LOGIN"):
        flash("Please wait before requesting a new OTP", "warning")
        return redirect(url_for("auth.verify_otp"))
    
    otp = create_otp(user, "FIRST_LOGIN")
    send_otp_email(user.email, otp, "FIRST_LOGIN")
    flash("New OTP sent successfully", "success")

    return redirect(url_for("auth.verify_otp"))


@auth_bp.route("/reset-password-start", methods = ['GET', 'POST'])
def reset_password_start():

    if request.method == 'POST':

        email = request.form.get("email")
        user = User.query.filter_by(email = email).first()

        if not user:
            flash("Email not found", "error")
            return redirect(url_for("auth.reset_password_start"))
        
        if not user.is_password_set:
            flash("Password not set yet. Use set password instead", "warning")
            return redirect(url_for("auth.set_password_start"))
        
        if not can_resend_otp(user, "RESET_PASSWORD"):
            flash("Please wait before requesting a new OTP", "warning")
            return redirect(url_for("auth.reset_password_start"))
        
        otp = create_otp(user, "RESET_PASSWORD")
        send_otp_email(user.email, otp, "RESET_PASSWORD")

        session["otp_user_email"] = email
        session["otp_verified"] = False

        flash("OTP sent to your registered email", 'success')

        return redirect(url_for("auth.verify_reset_otp"))
    
    return render_template("reset_password_start.html")


@auth_bp.route("/verify-reset-otp", methods = ['GET', 'POST'])
def verify_reset_otp():

    email = session.get("otp_user_email")

    if not email:
        flash("Session expired", "error")
        return redirect(url_for("auth.reset_password_start"))
    
    user = User.query.filter_by(email = email).first()

    if not user:
        flash("Invalid request", "error")
        return redirect(url_for("auth.login"))
    
    if request.method == 'POST':

        entered_otp = request.form.get("otp")
        entered_captcha = request.form.get("captcha")
        stored_captcha = session.get("captcha_text")

        if not stored_captcha or entered_captcha != stored_captcha:
            flash("Invalid captcha", "error")
            return redirect(url_for("auth.verify_reset_otp"))
        session.pop("captcha_text", None)

        success, message = verify_otp_code(user, entered_otp, "RESET_PASSWORD")

        if not success:
            flash(message, "error")
            return redirect(url_for("auth.verify_reset_otp"))
        
        session["otp_verified"] = True
        session["otp_verified_at"] = datetime.now(timezone.utc).isoformat()

        flash("OTP verified successfully")

        return redirect(url_for("auth.set_new_password"))
    
    latest_otp = UserOTP.query.filter_by(user_id = user.id, 
                                         purpose = "RESET_PASSWORD", is_used = False).order_by(UserOTP.created_at.desc()).first()
    
    remaining_seconds = 0

    if latest_otp:
        cooldown_end = latest_otp.created_at + timedelta(minutes=2)
        cooldown_end = ensure_utc(cooldown_end)
        remaining_seconds = max(0, int((cooldown_end - datetime.now(timezone.utc)).total_seconds())) 

    captcha_text = generate_captcha()
    session["captcha_text"] = captcha_text

    return render_template("verify_reset_otp.html", remaining_seconds = remaining_seconds, captcha_text = captcha_text)


@auth_bp.route("/set-new-password", methods = ['GET', 'POST'])
def set_new_password():

    email = session.get("otp_user_email")

    if not email:
        flash("Session expired", "error")
        return redirect(url_for("auth.reset_password_start"))
    
    if not session.get("otp_verified"):
        flash("Please verify OTP first", "error")
        return redirect(url_for("auth.verify_reset_otp"))
    
    user = User.query.filter_by(email = email).first()

    if not user:
        flash("Invalid requesst", "error")
        return redirect(url_for("auth.login"))
    
    if request.method == 'POST':

        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.set_new_password"))
        
        valid, message = validate_password_strength(password)

        if not valid:
            flash(message, "error")
            return redirect(url_for("auth.set_new_password"))
        
        user.set_password(password)

        UserOTP.query.filter_by(user_id = user.id, 
                                purpose = "RESET_PASSWORD", is_used = False).update({"is_used" : True})

        db.session.commit()
        session.clear()

        flash("Password reset successful, Please login", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("set_new_password.html")


@auth_bp.route("/resend-reset-otp")
def resend_reset_otp():

    email = session.get("otp_user_email")

    if not email:
        flash("Session expired", "error")
        return redirect(url_for("auth.reset_password_start"))
    
    user = User.query.filter_by(email = email).first()

    if not user:
        flash("Invalid request", "error")
        return redirect(url_for("auth.login"))
    
    if not can_resend_otp(user, "RESET_PASSWORD"):
        flash("Please wait before requesting a new OTP", "warning")
        return redirect(url_for("auth.verify_reset_otp"))
    
    otp = create_otp(user, "RESET_PASSWORD")
    send_otp_email(user.email, otp, "RESET_PASSWORD")
    flash("New OTP sent successfully", "success")

    return redirect(url_for("auth.verify_reset_otp"))