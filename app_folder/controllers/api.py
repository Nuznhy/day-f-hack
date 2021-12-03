import logging
from fastapi import APIRouter
from app_folder.schemas.api import ReadyResponse


ready_route = APIRouter()
log = logging.getLogger(__name__)


@ready_route.get(
    '/ready',
    tags=['ready'],
    response_model=ReadyResponse,
    summary="Simple health check."
)
def readiness_check():
    log.info("Started GET /ready")
    return ReadyResponse(status='ok')
