
import datetime
from sqlalchemy import Column, String, DateTime, Integer

from werkzeug.security import generate_password_hash, check_password_hash
from app_folder.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow())
    job = Column(String)
    image = Column(String)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.hashed_password = generate_password_hash(password)

    def verify_password(self, password_given):
        return check_password_hash(self.hashed_password, password_given)

