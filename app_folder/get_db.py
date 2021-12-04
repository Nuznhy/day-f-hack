from app_folder.database import SessionLocal
from contextvars import ContextVar
from sqlalchemy.orm import Session


async def get_db():
    with MySuperContextManager() as db:
        yield db


class MySuperContextManager:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()

