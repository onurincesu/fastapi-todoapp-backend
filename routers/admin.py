from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, HTTPException,status
import models
from database import Sessionlocal
from.auth import get_current_user


router=APIRouter(
    prefix="/admin",
    tags=["admin"]
)

def get_db():
    db=Sessionlocal()
    try:
        yield db 
    finally:
        db.close()

db_dependency=Annotated[Session,Depends(get_db)]
user_dependency=Annotated[dict,Depends(get_current_user)]

@router.get("/todo",status_code=status.HTTP_200_OK)
async def read_todos(user:user_dependency,db:db_dependency):
    if user is None or user.get("role")!="admin":
        raise HTTPException(status_code=401,detail="Authentication Failed")
    return db.query(models.Todos).all()

@router.delete("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user:user_dependency,db:db_dependency,todo_id:int):
    if user is None or user.get("role")!="admin":
         raise  HTTPException(status_code=403,detail="Forbidden")
    todo = db.query(models.Todos).filter(models.Todos.id==todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404,detail="Not Found")
    db.delete(todo)
    db.commit()
