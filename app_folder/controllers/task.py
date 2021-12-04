from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app_folder.get_db import get_db
from app_folder.crud.task import create_task_indb, get_task_by_id, get_all_tasks
from app_folder.schemas.task import TaskIn, TaskOut, FailResponse, AllTasksOut
from app_folder.tools.jwt_manage import get_current_active_user

task_route = APIRouter()


@task_route.post('/create', responses={200: {'model': TaskOut,
                                       'description': 'Created'}})
def create_task(task: TaskIn, db: Session = Depends(get_db),
                current_user=Depends(get_current_active_user)):
    task_result = create_task_indb(db=db, task=task, user_id=current_user.id)
    return task_result


@task_route.get('/get/{task_id}', responses={200: {'model': TaskOut,
                                                   'description': 'Shown'},
                                             404: {'model': FailResponse,
                                                   'description': 'id not found'}})
def show_by_id(task_id: int, db: Session = Depends(get_db),
               current_user=Depends(get_current_active_user)):
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id)
    if task is None:
        return JSONResponse(status_code=404, content={'success': False, 'message': 'Course with this ID not found'})
    return task


@task_route.get('/all',
                response_model=AllTasksOut)
def show_all_unfinished(per_page: Optional[int], page: Optional[int],
                        db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    return get_all_tasks(db=db, page=page, per_page=per_page, user_id=current_user.id)