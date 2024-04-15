from datetime import timedelta,datetime
from fastapi import APIRouter,Depends,HTTPException,status
from pydantic import BaseModel 
from models import Users
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from database import Sessionlocal
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

router=APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

SECRET_KEY="5ffc293ca729463a810c97cb276f8ca13437ef16dff685259ffaaf1daa250b7e"
ALGORITHM="HS256"

bcrypt_context=CryptContext(schemes=["bcrypt"], deprecated="auto")
oath2_bearer=OAuth2PasswordBearer(tokenUrl="auth/token")

def authenticate_user(username:str,password:str,db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not bcrypt_context.verify(password,user.password):
        return False
    return user

def create_access_token(username:str,user_id:int,role:str,expires_delta:timedelta):
    encode={"sub":username,"id":user_id, "role": role}
    expires=datetime.utcnow()+expires_delta
    encode.update({"exp":expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)
 
async def get_current_user(token:Annotated[str,Depends(oath2_bearer)]):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms= [ALGORITHM])
        username:str=payload.get("sub")
        user_id:int=payload.get("id")
        role:str=payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
        return{"username":username,"id":user_id,"role":role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate user.")


class CreateUserRequest(BaseModel):
    email:str 
    username:str
    firstname:str
    lastname:str
    password:str
    role:str

class Token(BaseModel):
    access_token:str
    token_type:str


def get_db():
    db=Sessionlocal()
    try:
        yield db
    finally:
        db.close()
        

db_dependency=Annotated[Session,Depends(get_db)]

@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency, 
                    create_user_request:CreateUserRequest):
    create_user_model=Users(
        email=create_user_request.email, 
        username=create_user_request.username,  
        firstname=create_user_request.firstname,  
        lastname=create_user_request.lastname,  
        password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role,
        is_active=True)
    db.add(create_user_model)
    db.commit()



    return create_user_model

@router.post("/token",response_model=Token)
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],
                                 db:db_dependency):
    user=authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate user.")
    token=create_access_token(user.username,user.id,user.role,timedelta(minutes=20))

    return {"access_token":token, "token_type":"bearer"}