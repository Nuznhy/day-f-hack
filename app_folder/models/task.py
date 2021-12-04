import datetime

from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey
from app_folder.database import Base


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    importance = Column(String)
    result = Column(Boolean, default=None)
    deadline = Column(DateTime, nullable=False)
    duration_of_completing = Column(DateTime, nullable=False)
    start_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())


class Hashtag(Base):
    __tablename__ = 'hashtags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)


class TaskHashtag(Base):
    __tablename__ = 'task-hashtag'

    task_id = Column(Integer, ForeignKey('tasks.id'), primary_key=True)
    hashtag_id = Column(Integer, ForeignKey('hashtags.id'), primary_key=True)


class UserHashtag(Base):
    __tablename__ = 'user-hashtag'

    hashtag_id = Column(Integer, ForeignKey('hashtags.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    color = Column(String, nullable=False)
