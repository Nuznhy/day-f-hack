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


class TaskHashtag(Base):
    __tablename__ = 'task_hashtag'

    task_id = Column(Integer, ForeignKey('tasks.id'), primary_key=True)
    hashtag_id = Column(Integer, ForeignKey('user_hashtag.id'), primary_key=True)


class UserHashtag(Base):
    __tablename__ = 'user_hashtag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    color = Column(String, nullable=False)
    background_color = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
