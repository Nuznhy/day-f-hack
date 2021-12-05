import datetime

from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
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
    deadline = Column(Float, nullable=False)
    duration_of_completing = Column(Float, nullable=False)
    start_time = Column(Float)
    created_at = Column(Float, default=datetime.datetime.utcnow().timestamp())
    completed_at = Column(Float, default=None)


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


class TaskRecommendation(Base):
    __tablename__ = 'task_recommendation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    recommended_time = Column(String)
