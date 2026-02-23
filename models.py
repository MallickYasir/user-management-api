




    # models.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# ========================================
# USER MODEL (for authentication)
# ========================================
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=100, unique=True)
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ========================================
# ITEM MODEL (your CRUD resource)
# ========================================
class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    price: float = Field(default=0.0, ge=0.0)  # ge = greater than or equal
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ========================================
# PYDANTIC MODELS (for API validation)
# ========================================
from pydantic import BaseModel, EmailStr

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool

class UserLogin(BaseModel):
    username: str
    password: str

# Item schemas
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

class ItemRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    owner_id: int