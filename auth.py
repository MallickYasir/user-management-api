# auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from models import User, UserCreate
from database import get_session
load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ========================================
# Password hashing functions
# ========================================
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

# ========================================
# JWT token functions
# ========================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    # Encode JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ========================================
# User authentication functions
# ========================================
async def authenticate_user(session: AsyncSession, username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password"""
    # Find user
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    """Create a new user"""
    # Check if user already exists
    existing_user = await get_user_by_username(session, user_create.username)
    if existing_user:
        raise ValueError("Username already exists")
    
    # Hash password
    hashed_password = hash_password(user_create.password)
    
    # Create user
    user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user

# ========================================
# Get current user from token (dependency)
# ========================================
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
  session: AsyncSession = Depends(get_session)
) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    
    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get username from token
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    # Get user from database
    user = await get_user_by_username(session, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    return user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if current user is superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user