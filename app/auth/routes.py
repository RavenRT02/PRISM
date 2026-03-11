from flask import Blueprint

auth_bp = Blueprint("auth", __name__)  # Blueprint(name_of_blueprint, location_of_files)

@auth_bp.route("/login")
def login():
    return "Login page"

