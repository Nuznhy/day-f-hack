from fastapi import APIRouter
from app_folder.controllers import api, auth, user, task

router_ready = APIRouter(prefix='/api')
router_ready.include_router(api.ready_route, tags=['ready'])

router_auth = APIRouter(prefix='/auth')
router_auth.include_router(auth.auth_route, tags=['auth'])

router_user = APIRouter(prefix='/user')
router_user.include_router(user.user_route, tags=['user'])

router_task = APIRouter(prefix='/task')
router_task.include_router(task.task_route, tags=['task'])