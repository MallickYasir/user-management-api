from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from contextlib import asynccontextmanager

from database import create_db_and_tables, get_session
from models import User

# 1. Lifespan context (runs on startup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# 2. Create App
app = FastAPI(lifespan=lifespan)

# 3. Create User Endpoint
@app.post("/users/")
def create_user(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# 4. Get All Users Endpoint
@app.get("/users/")
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users