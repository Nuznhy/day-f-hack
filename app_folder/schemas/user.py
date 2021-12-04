import uuid
from datetime import datetime
import re
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError, validator, Field
from typing import Optional


class UserBase(BaseModel):
    email: str


class UserLoginIn(UserBase):
    password: str

    class Config:
        schema_extra = {
            'example': {
                'email': 'email',
                'password': 'password'
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str
    success: bool


class TokenData(BaseModel):
    email: Optional[str] = None


class UserRegisterIn(BaseModel):
    email: str
    username: str
    password: str
    job: str
    first_name: Optional[str]
    last_name: Optional[str]
    image: Optional[str]

    @validator('username')
    def check_username(cls, value: str):
        if ' ' in value:
            raise ValueError('must not have spaces')
        return value

    @validator('password')
    def validate_password(cls, value: str):
        if not re.fullmatch(r'[A-Za-z0-9]{8,64}', value):
            raise ValueError('password must has at least 8 symbols, number and capital')
        return value

    @validator('email')
    def validate_email(cls, value: str):
        if ' ' in value:
            raise ValueError('not valid email')
        return value


class UserRegisterOut(BaseModel):
    success: bool
    access_token: str
    token_type: str

    class Config:
        schema_extra = {
            'example': {
                'success': True,
                'access_token': 'token',
                'token_type': 'Bearer',
            }
        }


class UserDataOut(BaseModel):
    id: int
    username: str
    email: str
    job: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    image: Optional[str] = None
    registration_date: float

    class Config:
        schema_extra = {
            'example': {
                'username': 'username',
                'password': 'password',
                'job': 'student',
                'first_name': 'Name',
                'last_name': 'Surname',
                'image': 'data:image/png;base64,blalblalba',
                'registration_date:': 'int'
                }
            }


class FailResponse(BaseModel):
    success: bool
    message: str
