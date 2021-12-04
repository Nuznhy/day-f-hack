from paginate_sqlalchemy import SqlalchemyOrmPage
from sqlalchemy import asc
from sqlalchemy.orm import Session
from app_folder.schemas.task import TaskIn, HashtagIn
from app_folder.models.tasks import Task, Hashtag


def create_task_indb(db: Session, task: TaskIn, user_id: int):
    task_record = Task(name=task.name, description=task.description, importance=task.importance,
                       deadline=task.deadline, duration_of_completing=task.duration_of_completing,
                       start_time=task.start_time, can_be_performed_after_dd=task.can_be_performed_after_dd,
                       user_id=user_id)
    db.add(task_record)
    db.commit()
    db.refresh(task_record)
    return task_record


def get_task_by_id(db: Session, task_id: int, user_id: int):
    return db.query(Task).filter_by(id=task_id, user_id=user_id).first()


def get_all_tasks(db: Session, user_id: int, page: int, per_page: int):
    task_query = db.query(Task).filter_by(user_id=user_id, result=None).order_by(asc(Task.deadline))
    pages = SqlalchemyOrmPage(task_query, page=page, db_session=db,
                              items_per_page=per_page)
    pagination = {'total': pages.item_count,
                  'pages': pages.page_count,
                  'tasks': [r.__dict__ for r in pages]}
    return pagination


def edit_task(db: Session, task_id: int, task: TaskIn, user_id: int):
    pass


def delete_task(db: Session, task_id: int, user_id: int):
    pass


# for Andre Stats
def get_all_undone_tasks(db: Session, user_id: int):
    return db.query(Task).filter_by(user_id=user_id, result=None).all()


# for Andre Stats
def get_all_done(db: Session, user_id: int):
    return db.query(Task).filter_by(user_id=user_id).filter(Task.result is not None).all()


def create_hashtag(db: Session, hashtag: HashtagIn):
    hashtag_record = Hashtag(name=hashtag.name)
    db.add(hashtag_record)
    db.commit()
    db.refresh(hashtag_record)
    return hashtag_record