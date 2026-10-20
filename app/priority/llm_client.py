# current app - gives access to the Flask application that is currently handling the operation.
# access the active application's configuration instead of loading config here again.

# flow .env file -- Stores environment variable names and values --> os.getenv() -- Retrieves values from the environment -->
# Config class -- Stores values as class attributes --> 
# app.config.from_object(Config) -- Loads uppercase attributes into Flask's dictionary-like configuration object -->
# current_app.config["LLM_API_KEY"] -- Retrieves a value from the active application's configuration


from flask import current_app     
from openai import OpenAI


def get_llm_client():
    """Create an API client using active Flask configuration"""

    config = current_app.config

    client_options = {
        "api_key" : config["LLM_API_KEY"]
    }

    if config.get("LLM_BASE_URL"):
        client_options["base_url"] = config["LLM_BASE_URL"]

    return OpenAI(**client_options)    # ** -- unpack client_options --> OpenAI(api_key, base_url)