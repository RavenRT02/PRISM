from flask_mail import Message
from flask import current_app
from app.extensions import mail


def send_email(subject, recipients, body):

    msg = Message(subject = subject, recipients = recipients, body = body)
    mail.send(msg)

def send_otp_email(recipient_email, otp, purpose):

    subject_map = {
        "FIRST_LOGIN" : "PRISM account setup OTP",
        "RESET PASSWORD" : "PRISM password reset OTP"
    }                                                       # purpose - subject ( dict keys - dict values )

    subject = subject_map.get(purpose, "PRISM verification OTP")   # default value "PRISM verification OTP" if key is missing

    body = f""" 
Hello, 

Your OTP for {purpose.replace("_"," ").title()} is: 
    
{otp}

This OTP will expire in 5 minutes

If you did not request this, Please ignore this email.

- PRISM Support System
"""
    send_email(subject = subject, recipients = [recipient_email], body = body)


