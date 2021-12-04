import datetime
import datetime as dt
from pytz import utc
from fastapi import Depends
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from sqlalchemy.orm import Session

from config import BASEDIR
from app_folder.models.tasks import Task
from app_folder.get_db import MySuperContextManager

jobstores = {
    'sqlite': SQLAlchemyJobStore(url='sqlite:///'+BASEDIR+'/jobs.db')
}
executors = {
    'default': ThreadPoolExecutor(1),
    'processpool': ProcessPoolExecutor(1)
}
job_defaults = {
  'coalesce': True,
  'max_instances': 1
}

scheduler_app = BackgroundScheduler()
scheduler_app.configure(jobstores=jobstores,
                        executors=executors,
                        job_defaults=job_defaults,
                        timezone=utc)


def mark_result_on_deadline(task_id: int):
    with MySuperContextManager() as db:
        task = db.query(Task).get(task_id)
        print('meme')
        if task is None:
            print('probleme')
            return False
        task.result = False
        db.add(task)
        db.commit()
        db.refresh(task)


def print_jobs_cron():
    meme_list = scheduler_app.get_jobs()
    for job in meme_list:
        print(job)
    print(datetime.datetime.utcnow().timestamp())
