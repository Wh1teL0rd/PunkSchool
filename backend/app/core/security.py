"""
Security utilities for authentication and authorization.
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    # PyJWT може повертати bytes, перетворюємо в string
    if isinstance(encoded_jwt, bytes):
        encoded_jwt = encoded_jwt.decode('utf-8')
    print(f"create_access_token: Created token for user_id {to_encode.get('sub')}, token: {encoded_jwt[:30]}...")
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token data or None if invalid
    """
    try:
        print(f"decode_token: Attempting to decode token with SECRET_KEY: {settings.SECRET_KEY[:10]}...")
        print(f"decode_token: Algorithm: {settings.ALGORITHM}")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"decode_token: Successfully decoded, payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError as e:
        print(f"Token decode error: Token expired - {e}")
        return None
    except jwt.DecodeError as e:
        print(f"Token decode error: Decode error - {e}")
        return None
    except jwt.InvalidSignatureError as e:
        print(f"Token decode error: Invalid signature - {e}")
        return None
    except InvalidTokenError as e:
        print(f"Token decode error: Invalid token - {e}")
        return None
    except Exception as e:
        print(f"Token decode error: Unexpected error {type(e).__name__}: {e}")
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Dependency to get current authenticated user from token.
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    from app.models.user import User
    from fastapi import Request
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        print("get_current_user: No token provided")
        raise credentials_exception
    
    # Видаляємо "Bearer " префікс якщо він є
    if token.startswith("Bearer "):
        token = token[7:]
    
    print(f"get_current_user: Received token (first 30 chars): {token[:30]}...")
    print(f"get_current_user: Token length: {len(token)}")
    
    payload = decode_token(token)
    if payload is None:
        print("get_current_user: Token decode failed")
        raise credentials_exception
    
    print(f"get_current_user: Token decoded successfully, payload: {payload}")
    user_id_str = payload.get("sub")
    if user_id_str is None:
        print("get_current_user: No 'sub' in payload")
        raise credentials_exception
    
    # Convert string back to int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        print(f"get_current_user: Invalid user_id format: {user_id_str}")
        raise credentials_exception
    
    print(f"get_current_user: Looking for user with id: {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"get_current_user: User with id {user_id} not found")
        raise credentials_exception
    
    print(f"get_current_user: User found: {user.email}, role: {user.role}")
    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Dependency to ensure user is active."""
    return current_user


def require_role(allowed_roles: list):
    """
    Dependency factory to require specific user roles.
    
    Args:
        allowed_roles: List of allowed UserRole values
    """
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
