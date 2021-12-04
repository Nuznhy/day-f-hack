from typing import Type, Any

from pydantic import BaseModel, ValidationError, validator


class TaskIn(BaseModel):
    name: str

    @validator('name')
    def validate(cls, value: Any):
        if value == '' or value is None:
            raise ValidationError('empty name')
        return value