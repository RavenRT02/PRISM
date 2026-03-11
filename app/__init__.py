from flask import Flask
from app.auth.routes import auth_bp 
from app.extensions import db,migrate

def create_app():

    app = Flask(__name__)
    app.config.from_object("app.config.Config")     # Use class directly instead of string method, Load configuration (settings for app) from the config file -> Config class
                                                    # Replaced app.config.from_object("app.config.Config") with app.config.from_object(Config)

    db.init_app(app)          # Attach db to flask app
    migrate.init(app , db)    # Attach migrate to flask app and connect with db         
                             
    app.register_blueprint(auth_bp)  # register / attach auth blueprint routes to main flask file

    return app