import os
from dotenv import load_dotenv

load_dotenv()

# flask configuration is conventionally represented as class

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")      # for testing, change later ! must load from .env (loads from env now)

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY not set")


    # Database config
    SQLALCHEMY_DATABASE_URI = "sqlite:///prism.db"  # /// to indicate local file , change after dev to bigger db
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Automated email config
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # LLM config 
    LLM_PROVIDER = os.getenv("LLM_PROVIDER")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL") or None