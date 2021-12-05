from fastapi import APIRouter, Depends

from app_folder.schemas.user import UserDataOut
from app_folder.tools.jwt_manage import get_current_active_user

user_route = APIRouter()


@user_route.get('/profile', response_model=UserDataOut)
async def read_users_me(current_user=Depends(get_current_active_user)):
    return current_user.__dict__