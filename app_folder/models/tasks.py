import datetime

from sqlalchemy import Column, String, Numeric, Integer, Boolean, ForeignKey
from app_folder.database import Base


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    importance = Column(Boolean, default=False)
    can_be_performed_after_dd = Column(Boolean, default=False)
    result = Column(Boolean, default=None)
    deadline = Column(Numeric, nullable=False)
    duration_of_completing = Column(Numeric, nullable=False)
    start_time = Column(Numeric)
    created_at = Column(Numeric, default=datetime.datetime.utcnow().timestamp())
    completed_at = Column(Numeric, default=None)


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
