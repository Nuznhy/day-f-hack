from fastapi import APIRouter
from app_folder.controllers import api

router_ready = APIRouter(prefix='/api')
router_ready.include_router(api.ready_route, tags=['ready'])