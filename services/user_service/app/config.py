import os

SECRET_KEY = os.environ.get("SECRET_KEY", "the_default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
