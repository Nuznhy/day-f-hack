from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette import status

from app_folder.get_db import get_db
from app_folder.schemas.user import UserRegisterIn, UserRegisterOut, Token, UserLoginIn, FailResponse
from app_folder.crud.user import get_user_by_email, register_user, get_user_by_username
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from app_folder.tools.jwt_manage import create_access_token, authenticate_user

auth_route = APIRouter()


@auth_route.post('/register',
                 response_model=UserRegisterOut,
                 responses={409: {'description': 'Validation error',
                                  'model': FailResponse}})
def register(user: UserRegisterIn, db: Session = Depends(get_db)):
    user_db = get_user_by_email(db=db, user_email=user.email) or get_user_by_username(db=db, username=user.username)
    if user_db is not None:
        return JSONResponse(status_code=409, content={'success': False, 'message': 'User registered'})
    user_record = register_user(db=db, user=user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_record.email}, expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'bearer', 'success': True}


@auth_route.post('/login', response_model=Token)
async def login_for_access_token(login_data: UserLoginIn, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", 'success': True}



