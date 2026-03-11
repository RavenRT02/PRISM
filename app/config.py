class Config:

    SECRET_KEY = "dev-secret-key"                   # for testing, change later !
    SQLALCHEMY_DATABASE_URI = "sqlite:///prism.db"  # /// to indicate local file , change after dev to bigger db
    SQLALCHEMY_TRACK_MODIFICATIONS = False