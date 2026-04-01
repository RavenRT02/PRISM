import random,hashlib
from datetime import datetime,timedelta,timezone
from app.extensions import db
from app.models import UserOTP

def generate_otp():

    return str(random.randint(100000, 999999))


def hash_otp(otp):

    return hashlib.sha256(otp.encode()).hexdigest()


def create_otp(user, purpose):                 # returns raw otp and stores hashed otp in db

    otp = generate_otp()

    otp_hash = hash_otp(otp)

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    otp_entry = UserOTP(user_id = user.id, otp_hash = otp_hash, purpose = purpose, expires_at = expires_at)

    db.session.add(otp_entry)
    db.session.commit()

    return otp


def get_active_otp(user, purpose):

    return UserOTP.query.filter_by(user_id = user.id, purpose = purpose, 
                                   is_used = False).order_by(UserOTP.created_at.desc()).first()  # return latest requested otp


def verify_otp(user, input_otp, purpose):

    otp_entry = get_active_otp(user, purpose)

    if not otp_entry:
        return False, "No active OTP found"
    
    if datetime.now(timezone.utc) > otp_entry.expires_at:
        return False, "OTP expired"
    
    if otp_entry.attempts >= 3:
        return False, "Maximum attempts exceeded"
    
    hashed_input = hash_otp(input_otp)

    if hashed_input != otp_entry.otp_hash:
        otp_entry.attempts += 1

        db.session.commit()
        return False, "Invalid OTP"
    
    otp_entry.is_used = True
    db.session.commit()

    return True, "OTP verified"


def can_resend_otp(user, purpose):

    otp_entry = get_active_otp(user, purpose)

    if not otp_entry:
        return True
    
    cooldown_time = otp_entry.created_at + timedelta(minutes=2)

    if datetime.now(timezone.utc) < cooldown_time:
        return False
    
    return True