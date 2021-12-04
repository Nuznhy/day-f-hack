import atexit
import logging
import socket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from config import PROJECT_NAME, DEBUG, VERSION
from app_folder.scheduler_tasks import scheduler_app

log = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


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

    @app.on_event('startup')
    def init_scheduler():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 47200))
        except socket.error:
            log.debug("!!!scheduler already started, DO NOTHING")
        else:
            scheduler_app.start()
            from app_folder.scheduler_tasks import print_jobs_cron
            scheduler_app.add_job(id='clear_daily_clicks',
                                  jobstore='sqlite',
                                  func=print_jobs_cron,
                                  trigger='cron',
                                  second=30,
                                  replace_existing=True)
            log.debug("Scheduler STARTED")
            jobs_list = scheduler_app.get_jobs()
            for job in jobs_list:
                print(job)

    @app.on_event('shutdown')
    def shutdown_scheduler():
        scheduler_app.shutdown()

    from routes import router_ready, router_auth, router_user, router_task
    app.include_router(router_ready)
    app.include_router(router_auth)
    app.include_router(router_user)
    app.include_router(router_task)
    log.debug("Add application routes.")
    return app


application = get_app()
