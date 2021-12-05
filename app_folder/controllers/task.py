import asyncio

from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app_folder.get_db import get_db
from app_folder.crud.task import create_add, get_task_by_id, get_all_tasks, task_remove, edit_task, task_complete, \
    get_all_done, get_all_undone_tasks, deadlines
from app_folder.schemas.task import TaskIn, TaskOut, FailResponse, AllTasksOut, AllTaskRecOut
from app_folder.tools.jwt_manage import get_current_active_user

task_route = APIRouter()


@task_route.post('/create', responses={200: {'model': FailResponse,
                                             'description': 'Updated'}})
def create_task(task: TaskIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                current_user=Depends(get_current_active_user)):
    task_id = create_add(db=db, task=task, user_id=current_user.id, background_tasks=background_tasks)
    return JSONResponse(status_code=200, content={'success': True, 'message': 'Task Created', 'task_id': task_id})


@task_route.get('/get/{task_id}', response_model=TaskOut, responses={
                                             404: {'model': FailResponse,
                                                   'description': 'id not found'}})
def show_by_id(task_id: int, db: Session = Depends(get_db),
               current_user=Depends(get_current_active_user)):
    task = get_task_by_id(db=db, task_id=task_id, user_id=current_user.id)
    if task is False:
        return JSONResponse(status_code=404, content={'success': False, 'message': 'Course with this ID not found'})
    return task


@task_route.get('/all',
                response_model=AllTasksOut)
def show_all(per_page: Optional[int] = 20, page: Optional[int] = 1, pending: Optional[bool] = True,
             db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    return get_all_tasks(db=db, page=page, per_page=per_page, user_id=current_user.id, pending=pending)


@task_route.patch('/edit/{task_id}',
                  responses={200: {'model': FailResponse,
                                   'description': 'Updated'},
                             404: {'model': FailResponse,
                                   'description': 'id not found'}})
def edit(task: TaskIn, task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    result = edit_task(db=db, task_new=task, task_id=task_id, user_id=current_user.id)
    if result:
        return JSONResponse(status_code=200, content={'success': True, 'message': 'Task Edited'})
    return JSONResponse(status_code=404, content={'success': False, 'message': 'Task with this ID not found'})


@task_route.delete('/delete/{task_id}', responses={200: {'model': FailResponse,
                                                   'description': 'Shown'},
                                                   404: {'model': FailResponse,
                                                   'description': 'id not found'}})
def delete_task(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    result = task_remove(db=db, task_id=task_id, user_id=current_user.id)
    if result:
        return JSONResponse(status_code=200, content={'success': True, 'message': 'Task Removed'})
    return JSONResponse(status_code=404, content={'success': False, 'message': 'Task with this ID not found'})


@task_route.post('/mark-completed/{task_id}', responses={200: {'model': FailResponse,
                                                               'description': 'Shown'},
                                                         404: {'model': FailResponse,
                                                               'description': 'id not found'}})
def task_mark_completed(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    result = task_complete(db=db, task_id=task_id, user_id=current_user.id)
    if result:
        return JSONResponse(status_code=200, content={'success': True, 'message': 'Task Completed'})
    return JSONResponse(status_code=404, content={'success': False, 'message': 'Task with this ID not found'})


@task_route.get('/get-recommendations', response_model=AllTaskRecOut)
def show_recommendations(db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    result = deadlines(db=db, user_id=current_user.id)
    return result