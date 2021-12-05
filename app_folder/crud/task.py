import logging
import random
import datetime as dt
from copy import deepcopy

from paginate_sqlalchemy import SqlalchemyOrmPage
from fastapi import BackgroundTasks
from apscheduler.jobstores.base import JobLookupError
from sqlalchemy import asc
from sqlalchemy.orm import Session
import numpy as np
from app_folder.schemas.task import TaskIn
from app_folder.models.tasks import Task, TaskHashtag, UserHashtag, TaskRecommendation
from app_folder.scheduler_tasks import scheduler_app, mark_result_on_deadline
from app_folder.logic.greedy_priority import Scheduling

colors = [('428DFD', 'B6D3FF'), ('39E769', 'B6FFC6'), ('E9E444', 'FEFFB6'), ('D01BFD', 'F5B6FF'), ('FD42B2', 'FFB6F8'),
          ('FD8542', 'FFD0B6'), ('FD5842', 'FFBAB6'), ('9442FD', 'E8B6FF'), ('FD4242', 'FFB6B6'), ('42FDAE', 'B6FFCA'),
          ('5142FD', 'C4B6FF'), ('42DBFD', 'B6F2FF')]


def calculate_new_recommendations(db: Session, user_id: int):
    done_tasks = get_all_done(db, user_id)
    undone_tasks = get_all_undone_tasks(db, user_id)
    # Andre part
    calculations = Scheduling()
    recommendation = calculations.tasksScheduling(undone_tasks, done_tasks)
    # Not Andre part
    old_recommendations = db.query(TaskRecommendation).filter_by(user_id=user_id).all()
    for old_rec in old_recommendations:
        db.delete(old_rec)
    for rec in recommendation:
        np_int = np.int64(rec['id_task'])
        id_task = np_int.item()
        recommendation = TaskRecommendation(task_id=id_task, user_id=user_id,
                                            recommended_time=rec['recommended_time'])
        db.add(recommendation)
    db.commit()


def create_add(db: Session, task: TaskIn, user_id: int, background_tasks: BackgroundTasks):
    task_record = Task(name=task.name, description=task.description, importance=task.importance, user_id=user_id,
                       deadline=task.deadline, duration_of_completing=task.duration_of_completing,
                       start_time=task.start_time, can_be_performed_after_dd=task.can_be_performed_after_dd)
    db.add(task_record)
    db.commit()
    if task.can_be_performed_after_dd is False:
        scheduler_app.add_job(id='deadline_to_task_{}'.format(task_record.id), jobstore='sqlite', trigger='date',
                              func=mark_result_on_deadline, run_date=dt.datetime.utcfromtimestamp(task.deadline),
                              args=[task_record.id], misfire_grace_time=None)
    meme_list = scheduler_app.get_jobs()
    for job in meme_list:
        print(job)
    hashtags = []
    for tag_name in task.hashtags:
        user_tag = db.query(UserHashtag).filter_by(name=tag_name).first()
        if user_tag is None:
            color = random.choice(colors)
            user_tag = UserHashtag(name=tag_name, user_id=user_id, color=color[0], background_color=color[1])
            db.add(user_tag)
            db.commit()

        hashtags.append(user_tag.__dict__)
        tag_task = db.query(TaskHashtag).get((task_record.id, user_tag.id))
        if tag_task is None:
            tag_task = TaskHashtag(task_id=task_record.id, hashtag_id=user_tag.id)
            db.add(tag_task)
    db.commit()
    db.refresh(task_record)
    background_tasks.add_task(calculate_new_recommendations, db, user_id)
    return task_record.id


def get_task_by_id(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if task is None:
        return False
    task = task.__dict__
    tasks_hashtags_ids = [tag.hashtag_id for tag in
                          db.query(TaskHashtag).with_entities(TaskHashtag.hashtag_id).filter_by(task_id=task['id'])]
    pk = UserHashtag.__mapper__.primary_key[0]
    hashtags = db.query(UserHashtag).filter(pk.in_(tasks_hashtags_ids))
    task.update({'hashtags': [r.__dict__ for r in hashtags]})
    return task


def get_all_tasks(db: Session, user_id: int, page: int, per_page: int, pending: bool):
    task_query = db.query(Task).filter_by(user_id=user_id, result=None).order_by(asc(Task.deadline))
    if pending is False:
        task_query = db.query(Task).filter_by(user_id=user_id).filter(Task.result != None).order_by(asc(Task.deadline))

    pages = SqlalchemyOrmPage(task_query, page=page, db_session=db,
                              items_per_page=per_page)
    tasks = [r.__dict__ for r in pages]
    for task in tasks:
        tasks_hashtags_ids = [tag.hashtag_id for tag in
                              db.query(TaskHashtag).with_entities(TaskHashtag.hashtag_id).filter_by(task_id=task['id'])]
        pk = UserHashtag.__mapper__.primary_key[0]
        hashtags = db.query(UserHashtag).filter(pk.in_(tasks_hashtags_ids))
        task.update({'hashtags': [r.__dict__ for r in hashtags]})
    pagination = {'total': pages.item_count, 'pages': pages.page_count,
                  'tasks': tasks}
    return pagination


def edit_task(db: Session, task_id: int, task_new: TaskIn, user_id: int):
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if task is None:
        return False
    task.name = task_new.name
    task.description = task_new.description
    task.importance = task_new.importance
    task.can_be_performed_after_dd = task_new.can_be_performed_after_dd
    db.add(task)
    db.commit()
    return True


def task_remove(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if task is None:
        return False

    task_tags = db.query(TaskHashtag).filter_by(task_id=task_id).all()
    for tag in task_tags:
        db.delete(tag)

    try:
        scheduler_app.remove_job('deadline_to_task_{}'.format(task.id))
    except JobLookupError as e:
        print(e)
        pass
    db.commit()
    db.delete(task)
    db.commit()
    return True


def task_complete(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if task is None:
        return False
    task.result = True
    task.completed_at = dt.datetime.utcnow().timestamp()
    db.add(task)
    db.commit()
    return True


# for Andre Stats
def get_all_undone_tasks(db: Session, user_id: int):
    task_res_none = db.query(Task).filter_by(user_id=user_id, result=None).order_by(asc(Task.deadline)).all()
    result_list = []
    for task in task_res_none:
        if task.id == -1:
            continue
        tasks_hashtags_ids = [tag.hashtag_id for tag in
                              db.query(TaskHashtag).with_entities(TaskHashtag.hashtag_id).filter_by(task_id=task.id)]
        pk = UserHashtag.__mapper__.primary_key[0]
        hashtags = db.query(UserHashtag).filter(pk.in_(tasks_hashtags_ids))

        tags = [r.__dict__['name'] for r in hashtags]
        tags_string = ' '.join(tags)

        task_dict = {'id': task.id,
                     'name': task.name,
                     'user_id': task.user_id,
                     'description': task.description,
                     'importance': task.importance,
                     'can_be_performed_after_dd': task.can_be_performed_after_dd,
                     'result': task.result,
                     'deadline': task.deadline,
                     'duration_of_completing': task.duration_of_completing,
                     'start_time': task.start_time,
                     'created_at': task.created_at,
                     'completed_at': task.completed_at}
        task_dict.update({'hashtags': tags_string})
        result_list.append(task_dict)
    return result_list


# for Andre Stats
def get_all_done(db: Session, user_id: int):
    task_res_not_none = db.query(Task).filter_by(user_id=user_id).filter(Task.result != None).order_by(asc(Task.deadline)).all()
    result_list = []
    for task in task_res_not_none:
        tasks_hashtags_ids = [tag.hashtag_id for tag in
                              db.query(TaskHashtag).with_entities(TaskHashtag.hashtag_id).filter_by(task_id=task.id)]
        pk = UserHashtag.__mapper__.primary_key[0]
        hashtags = db.query(UserHashtag).filter(pk.in_(tasks_hashtags_ids))

        tags = [r.__dict__['name'] for r in hashtags]
        tags_string = ' '.join(tags)

        task_dict = {'id': task.id,
                     'name': task.name,
                     'user_id': task.user_id,
                     'description': task.description,
                     'importance': task.importance,
                     'can_be_performed_after_dd': task.can_be_performed_after_dd,
                     'result': task.result,
                     'deadline': task.deadline,
                     'duration_of_completing': task.duration_of_completing,
                     'start_time': task.start_time,
                     'created_at': task.created_at,
                     'completed_at': task.completed_at}

        task_dict.update({'hashtags': tags_string})
        result_list.append(task_dict)
    return result_list


def deadlines(db: Session, user_id: int):
    recommendations = db.query(TaskRecommendation).filter_by(user_id=user_id).\
        order_by(TaskRecommendation.recommended_time)
    result_list = []
    for rec in recommendations:
        task = db.query(Task).get(rec.task_id)
        if task is not None:
            task_dict = deepcopy(task.__dict__)
            tasks_hashtags_ids = [tag.hashtag_id for tag in
                                  db.query(TaskHashtag).with_entities(TaskHashtag.hashtag_id).filter_by(task_id=task.id)]
            pk = UserHashtag.__mapper__.primary_key[0]
            hashtags = db.query(UserHashtag).filter(pk.in_(tasks_hashtags_ids))

            hashtags_list = []
            for tag in hashtags:
                hashtags_list.append({'color': tag.color,
                                      'background_color': tag.background_color,
                                      'name': tag.name})

            task_dict.update({'recommendation': rec.recommended_time, 'hashtags': hashtags_list})

            result_list.append(task_dict)
    return {'tasks': result_list}
