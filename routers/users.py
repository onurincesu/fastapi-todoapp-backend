
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, HTTPException,status
import models
from database import Sessionlocal
from.auth import get_current_user
from passlib.context import CryptContext

router=APIRouter(
    prefix= "/user",
    tags=["user"]
)

def get_db():
    db=Sessionlocal()
    try:
        yield db 
    finally:
        db.close()

db_dependency=Annotated[Session,Depends(get_db)]
user_dependency=Annotated[dict,Depends(get_current_user)]
bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

class verification(BaseModel):
    password:str
    new_password:str

@router.get("/",status_code=status.HTTP_200_OK)
async def get_user(user:user_dependency,db:db_dependency):
    if user is None:
        raise  HTTPException(status_code=400,detail="User not found.")
    return db.query(models.Users).filter(models.Users.id==user.get("id")).first()

@router.put("/password",status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user:user_dependency,verification:verification,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=401,detail= "Not authenticated user.")
    user_model=db.query(models.Users).filter(models.Users.id==user.get("id")).first()

    if not bcrypt_context.verify(verification.password,user_model.password):
        raise HTTPException(status_code=401,detail="Wrong Password")
    
    user_model.password=bcrypt_context.hash(verification.new_password)
    db.add(user_model)
    db.commit()