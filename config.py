import os

import cloudinary

from version import __version__
# FastAPI logging level
DEBUG = True
# FastAPI project name
PROJECT_NAME = "day-f-hack"
VERSION = __version__
# Path to config file
BASEDIR = os.path.abspath(os.path.dirname(__file__))
SECRET_KEY = 'e2f82a6ee04556df6146776dac7a08568973f97fc41be1bc5eea7d70ee709cd2'
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

cloudinary.config(
  cloud_name="hyrxwqaad",
  api_key="926682174261518",
  api_secret="vtmk2vUaapq9jVZY_QNxtbr6mTw"
)
