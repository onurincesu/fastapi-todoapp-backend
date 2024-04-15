from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, HTTPException,status
import models
from database import Sessionlocal
from.auth import get_current_user
from fastapi.responses import HTMLResponse



router=APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404:{ "description":"Not found"}}
)



def get_db():
    db=Sessionlocal()
    try:
        yield db 
    finally:
        db.close()

db_dependency=Annotated[Session,Depends(get_db)]
user_dependency=Annotated[dict,Depends(get_current_user)]

class TodoRequest(BaseModel):
    title:str
    description:str
    priority:int
    complete:bool

 
@router.get("/")
async def read_all(user:user_dependency,db:db_dependency,status_code=status.HTTP_200_OK):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")

    return db.query(models.Todos).filter(models.Todos.ownerid==user.get("id")).all()


@router.get("/todo/{todo_id}",status_code=status.HTTP_200_OK)
async def  read_todo(user:user_dependency,db:db_dependency,todo_id:int):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    
    model= db.query(models.Todos).filter(models.Todos.id==todo_id)\
        .filter(models.Todos.ownerid==user.get("id")).first()

    if model is not None:
        return model
    else:
        raise HTTPException(status_code=404,detail="Not found")


@router.post("/todo/")
async def create_todo(user:user_dependency
                      ,request:TodoRequest,db:db_dependency):
    
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    todo_model=models.Todos(**request.model_dump(),ownerid=user.get("id"))
    
    db.add(todo_model)
    db.commit()


@router.put("/todos/put")
async def update_base(user:user_dependency,db:db_dependency,request:TodoRequest,id:int):

    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")

    todo=db.query(models.Todos).filter(models.Todos.id == id)\
        .filter(models.Todos.ownerid==user.get("id")).first()

    if todo :
        todo.title=request.title
        todo.description=request.description
        todo.priority=request.priority
        todo.complete=request.complete
        
        db.add(todo)
        db.commit()
        return {"message": "Updated"}
    else:
        raise HTTPException(status_code=404, detail="Task with this ID does not exist.")


@router.delete("/todo/delete")
async def delete_task(user:user_dependency,db:db_dependency,id:int):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    
    todo_model=db.query(models.Todos).filter(models.Todos.id==id)\
        .filter(models.Todos.ownerid==user.get("id")).first()
    
    if todo_model is None:
        raise HTTPException(status_code=404,detail="Todo not found.")
    
    db.delete(todo_model)
    db.commit()


