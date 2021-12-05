import datetime
import datetime as dt
from pytz import utc
from fastapi import Depends
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from sqlalchemy import asc
from sqlalchemy.orm import Session

from config import BASEDIR

from app_folder.models.tasks import Task, TaskRecommendation, TaskHashtag, UserHashtag
from app_folder.get_db import MySuperContextManager
from app_folder.logic.greedy_priority import Scheduling

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


def update_recs():
    with MySuperContextManager() as db:
        from models.users import User
        for user in db.query(User).all():
            user_id = user.id
            done_tasks = get_all_undone_tasks_for_sched(db, user_id)
            undone_tasks = get_all_done_for_sched(db, user_id)
            # Andre part
            try:
                calculations = Scheduling()
                recommendation = calculations.tasksScheduling(undone_tasks, done_tasks)
                # Not Andre part
                old_recommendations = db.query(TaskRecommendation).filter_by(user_id=user_id).all()
                for old_rec in old_recommendations:
                    db.delete(old_rec)
                for rec in recommendation:
                    recommendation = TaskRecommendation(task_id=rec['id_task'], user_id=user_id,
                                                        recommended_time=rec['recommended_time'])
                    db.add(recommendation)
                db.commit()
            except KeyError:
                pass


# for Andre Stats
def get_all_undone_tasks_for_sched(db: Session, user_id: int):
    task_res_none = db.query(Task).filter_by(user_id=user_id, result=None).order_by(asc(Task.deadline)).all()

    result_list = []
    for task in task_res_none:
        tasks_hashtags_ids = [tag.hashtag_id for tag in
                              db.query(TaskHashtag).with_entities(TaskHashtag.hashtag_id).filter_by(task_id=task.id)]
        pk = UserHashtag.__mapper__.primary_key[0]
        hashtags = db.query(UserHashtag).filter(pk.in_(tasks_hashtags_ids))

        tags = [r.__dict__['name'] for r in hashtags]
        tags_string = ' '.join(tags)

        task_dict = task.__dict__
        task_dict.update({'hashtags': tags_string})
        result_list.append(task_dict)
    return result_list


# for Andre Stats
def get_all_done_for_sched(db: Session, user_id: int):
    task_res_not_none = db.query(Task).filter_by(user_id=user_id).filter(Task.result != None).order_by(asc(Task.deadline)).all()
    result_list = []
    for task in task_res_not_none:
        tasks_hashtags_ids = [tag.hashtag_id for tag in
                              db.query(TaskHashtag).with_entities(TaskHashtag.hashtag_id).filter_by(task_id=task.id)]
        pk = UserHashtag.__mapper__.primary_key[0]
        hashtags = db.query(UserHashtag).filter(pk.in_(tasks_hashtags_ids))

        tags = [r.__dict__['name'] for r in hashtags]
        tags_string = ' '.join(tags)

        task_dict = task.__dict__
        task_dict.update({'hashtags': tags_string})
        result_list.append(task_dict)
    return result_list


def print_jobs_cron():
    meme_list = scheduler_app.get_jobs()
    for job in meme_list:
        print(job)
    print(datetime.datetime.utcnow().timestamp())
