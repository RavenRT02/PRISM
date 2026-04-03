import random
import string

def generate_captcha(length = 5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k = length))