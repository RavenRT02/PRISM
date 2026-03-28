from flask import Flask
from app.auth.routes import auth_bp 
from app.extensions import db,migrate,login_manager
from app import models
from app.org_setup.routes import org_bp

def create_app():

    app = Flask(__name__)
    app.config.from_object("app.config.Config")     # Use class directly instead of string method, Load configuration (settings for app) from the config file -> Config class
                                                    # Replaced app.config.from_object("app.config.Config") with app.config.from_object(Config)

    db.init_app(app)          # Attach db to flask app
    migrate.init_app(app , db)    # Attach migrate to flask app and connect with db      
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"   # uses login path in auth/routes.py 

    app.register_blueprint(auth_bp)  # register / attach auth blueprint routes to main flask file
    app.register_blueprint(org_bp)

    return app