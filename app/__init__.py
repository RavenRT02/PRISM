from flask import Flask
from app.auth.routes import auth_bp 

def create_app():

    app = Flask(__name__)
    app.config.from_object("app.config.Config")     # Load configuration (settings for app) from the config file -> Config class
    app.register_blueprint(auth_bp)  # register / attach auth blueprint routes to main flask file

    return app