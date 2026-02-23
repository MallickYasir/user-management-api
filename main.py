# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from datetime import timedelta
import os
from dotenv import load_dotenv

# Import local modules
import database
import auth
from models import (
    UserCreate, UserRead, UserLogin,
    ItemCreate, ItemUpdate, ItemRead,
    User, Item
)
from sqlmodel import select

load_dotenv()

# ========================================
# Create FastAPI app
# ========================================
app = FastAPI(
    title=os.getenv("APP_NAME", "FastAPI MySQL API"),
    description="Secure CRUD API with JWT authentication",
    version="1.0.0"
)

# ========================================
# Startup event (create tables)
# ========================================
@app.on_event("startup")
async def on_startup():
    await database.init_db()

# ========================================
# Health check endpoint
# ========================================
@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI MySQL API",
        "status": "running",
        "docs": "/docs"
    }

# ========================================
# AUTH ENDPOINTS
# ========================================

@app.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, session: AsyncSession = Depends(database.get_session)):
    """Register a new user"""
    try:
        user = await auth.create_user(session, user_create)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login(
    user_login: UserLogin,
    session: AsyncSession = Depends(database.get_session)
):
    """Login and get JWT token"""
    user = await auth.authenticate_user(session, user_login.username, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }

# ========================================
# ITEM CRUD ENDPOINTS (PROTECTED)
# ========================================

@app.post("/items/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_create: ItemCreate,
    current_user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(database.get_session)
):
    """Create a new item (requires authentication)"""
    item = Item(
        **item_create.dict(),
        owner_id=current_user.id
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

@app.get("/items/", response_model=List[ItemRead])
async def read_items(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(database.get_session)
):
    """Get all items for current user"""
    statement = select(Item).where(Item.owner_id == current_user.id).offset(skip).limit(limit)
    result = await session.execute(statement)
    items = result.scalars().all()
    return items

@app.get("/items/{item_id}", response_model=ItemRead)
async def read_item(
    item_id: int,
    current_user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(database.get_session)
):
    """Get a specific item by ID"""
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check ownership
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return item

@app.put("/items/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    current_user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(database.get_session)
):
    """Update an item"""
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check ownership
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update fields
    for key, value in item_update.dict(exclude_unset=True).items():
        setattr(item, key, value)
    
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    current_user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(database.get_session)
):
    """Delete an item"""
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check ownership
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    await session.delete(item)
    await session.commit()
    
    return {"message": "Item deleted successfully"}

# ========================================
# ADMIN ENDPOINT (superuser only)
# ========================================

@app.get("/admin/users", response_model=List[UserRead])
async def list_all_users(
    current_user: User = Depends(auth.get_current_active_superuser),
    session: AsyncSession = Depends(database.get_session)
):
    """List all users (admin only)"""
    statement = select(User)
    result = await session.execute(statement)
    users = result.scalars().all()
    return users