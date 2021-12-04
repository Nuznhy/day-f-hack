import datetime as dt
from typing import Any, Optional, List
from pydantic import BaseModel, validator, root_validator


class TaskIn(BaseModel):
    name: str
    description: Optional[str]
    importance: Optional[bool]
    can_be_performed_after_dd: Optional[bool]
    deadline: float
    duration_of_completing: Optional[float]
    start_time: Optional[float]
    hashtags: List[str]

    @validator('name')
    def validate_name(cls, value: Any):
        if value == '' or ' ' in value or value is None:
            raise ValueError('empty name')
        return value

    @validator('deadline')
    def validate_deadline(cls, value: float):
        if value < dt.datetime.utcnow().timestamp():
            raise ValueError('deadline already passed')
        return value

    @validator('start_time')
    def validate_start_time(cls, value: float):
        if value < dt.datetime.utcnow().timestamp():
            raise ValueError('start_time already passed')
        return value

    @validator('hashtags')
    def validate_hashtags(cls, value):
        if len(value) == 0:
            raise ValueError('must have at least one hashtag')
        for tag in value:
            if tag[0] != '#' or ' ' in tag:
                raise ValueError(tag+' is not valid hashtag')
        return value

    @root_validator()
    def validate_duration_time(cls, values):
        deadline, duration_of_completing, start_time = values.get('deadline'), \
                                                       values.get('duration_of_completing'), values.get('start_time')
        if start_time is None:
            start_time = dt.datetime.utcnow().timestamp()
        if duration_of_completing > deadline - start_time:
            raise ValueError('duration_of_completing is too long, please start earlier')
        return values

    class Config:
        schema_extra = {
            'example': {
                'name': 'name',
                'description': 'description',
                'importance': True,
                'can_be_performed_after_dd': True,
                'deadline': 'timestamp',
                'duration_of_completing': '1638606071.166601',
                'start_time': '1638606071.166601'
            }
        }


class HashTagOut(BaseModel):
    name: str
    color: str
    background_color: str


class TaskOut(BaseModel):
    id: int = None
    user_id: int = None
    name: str = None
    description: Optional[str] = None
    importance: bool = None
    can_be_performed_after_dd: bool = None
    deadline: float = None
    duration_of_completing: Optional[float] = None
    start_time: Optional[float] = None
    result: bool = None
    created_at: float = None
    completed_at: float = None
    hashtags: List[HashTagOut]


class AllTasksOut(BaseModel):
    total: int
    pages: int
    tasks: Optional[List[TaskOut]]


class FailResponse(BaseModel):
    success: bool
    message: str


class TaskCreateResponse(FailResponse):
    task_id: int