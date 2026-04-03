import re 

def validate_password_strength(password):

    errors = []

    if len(password) < 8 or len(password) > 16:
        errors.append("Password must be between 8 and 16 characters")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain atleast one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain atleast one lowercase letter")
    
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain atleast one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain atleast one special character")
    
    if errors:
        return False, errors
    
    return True, None