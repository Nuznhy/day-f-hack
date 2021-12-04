from contextvars import ContextVar
import random
import datetime as dt
from paginate_sqlalchemy import SqlalchemyOrmPage
from sqlalchemy import asc
from sqlalchemy.orm import Session
from app_folder.schemas.task import TaskIn
from app_folder.models.tasks import Task, TaskHashtag, UserHashtag
from app_folder.scheduler_tasks import scheduler_app, mark_result_on_deadline

colors = [('428DFD', 'B6D3FF'), ('39E769', 'B6FFC6'), ('E9E444', 'FEFFB6'), ('D01BFD', 'F5B6FF'), ('FD42B2', 'FFB6F8'),
          ('FD8542', 'FFD0B6'), ('FD5842', 'FFBAB6'), ('9442FD', 'E8B6FF'), ('FD4242', 'FFB6B6'), ('42FDAE', 'B6FFCA'),
          ('5142FD', 'C4B6FF'), ('42DBFD', 'B6F2FF')]


def create_add(db: Session, task: TaskIn, user_id: int):
    task_record = Task(name=task.name, description=task.description, importance=task.importance,
                       deadline=task.deadline, duration_of_completing=task.duration_of_completing,
                       start_time=task.start_time, can_be_performed_after_dd=task.can_be_performed_after_dd,
                       user_id=user_id)
    db.add(task_record)
    db.commit()
    db.refresh(task_record)
    if task.can_be_performed_after_dd is False:
        scheduler_app.add_job(id='deadline_to_task_{}'.format(task_record.id),
                              jobstore='sqlite',
                              func=mark_result_on_deadline,
                              trigger='date',
                              run_date=dt.datetime.utcfromtimestamp(task.deadline),
                              args=[task_record.id],
                              misfire_grace_time=None)
    meme_list = scheduler_app.get_jobs()
    for job in meme_list:
        print(job)
    hashtags = []
    for tag_name in task.hashtags:
        user_tag = db.query(UserHashtag).filter_by(name=tag_name).first()
        if user_tag is None:
            color = random.choice(colors)
            user_tag = UserHashtag(name=tag_name, user_id=user_id,
                                   color=color[0], background_color=color[1])
            db.add(user_tag)
            db.commit()
            db.refresh(user_tag)
        hashtags.append(user_tag.__dict__)
        tag_task = db.query(TaskHashtag).get((task_record.id, user_tag.id))
        if tag_task is None:
            tag_task = TaskHashtag(task_id=task_record.id, hashtag_id=user_tag.id)
            db.add(tag_task)
            db.commit()
            db.refresh(tag_task)
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
    db.refresh(task)
    return True


def task_remove(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if task is None:
        return False

    task_tags = db.query(TaskHashtag).filter_by(task_id=task_id).all()
    for tag in task_tags:
        db.delete(tag)
        db.commit()
    db.delete(task)
    db.commit()
    return True


def task_complete(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if task is None:
        return False
    task.result = True
    db.add(task)
    db.commit()
    db.refresh(task)
    return True


# for Andre Stats
def get_all_undone_tasks(db: Session, user_id: int):
    task_res_none = db.query(Task).filter_by(user_id=user_id, result=None).order_by(asc(Task.deadline)).all()

    tasks_res_none = [r.__dict__ for r in task_res_none]
    result_list = []
    for task in tasks_res_none:
        tasks_hashtags_ids = [tag.hashtag_id for tag in
                              db.query(TaskHashtag).with_entities(TaskHashtag.hashtag_id).filter_by(task_id=task['id'])]
        pk = UserHashtag.__mapper__.primary_key[0]
        hashtags = db.query(UserHashtag).filter(pk.in_(tasks_hashtags_ids))

        tags = [r.__dict__['name'] for r in hashtags]
        tags_string = ' '.join(tags)

        task_dict = task.__dict__
        task_dict.update({'hashtags': tags_string})
        result_list.append(task_dict)
    return tasks_res_none


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

        task_dict = task.__dict__
        task_dict.update({'hashtags': tags_string})
        result_list.append(task_dict)
    return result_list
