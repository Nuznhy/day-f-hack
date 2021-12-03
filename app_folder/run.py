import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router_ready
from config import PROJECT_NAME, DEBUG, VERSION
log = logging.getLogger(__name__)


def get_app():
    """Initialize FastAPI application.
    Returns:
        app (FastAPI): Application object instance.
    """
    log.debug("Initialize FastAPI application node.")

    app = FastAPI(
        title=PROJECT_NAME,
        debug=DEBUG,
        version=VERSION,
        docs_url="/swagger",
    )

    origins = [
        "http://localhost",
        "http://localhost:8080",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router_ready)

    log.debug("Add application routes.")
    return app


application = get_app()