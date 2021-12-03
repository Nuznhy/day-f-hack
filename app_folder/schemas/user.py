from datetime import datetime
import re

from pydantic import BaseModel, ValidationError, validator
from typing import Optional


class UserBase(BaseModel):
    email: str


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
    def username_validate(name):
        if ' ' in name:
            raise ValidationError('must not have spaces')
        return name

    @validator('password')
    def password_validate(password):
        if not re.fullmatch(r'[A-Za-z0-9]{8,}', str(password)):
            raise ValidationError('password must has at least 8 symbols, number and capital')
        return password

    class Config:
        schema_extra = {
            'example': {
                'success': True,
                'access_token': 'token',
                'token_type': 'Bearer',
            }
        }


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
    username: str
    email: str
    job: str
    first_name: Optional[str]
    last_name: Optional[str]
    image: Optional[str]
    registration_date: Optional[datetime]

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


class UserLoginIn(UserBase):
    password: str

    class Config:
        schema_extra = {
            'example': {
                'email': 'email',
                'password': 'password'
            }
        }


class FailResponse(BaseModel):
    success: bool
    message: str