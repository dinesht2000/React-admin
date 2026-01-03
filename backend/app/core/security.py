#Security utilities for password hashing and JWT token management.
#Uses bcrypt for password hashing and python-jose for JWT tokens.

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import SECRET_KEY, ALGORITHM

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:

    # Verify a plain text password against a bcrypt hash.
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:

    # Hash a password using bcrypt.
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    
    # Create a JWT access token with expiration.
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:

    # Decode and verify JWT token signature and expiration.
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_role_from_token(token: str) -> Optional[str]:

    # Extract account role from JWT token payload.

    payload = decode_token(token)
    if payload:
        return payload.get("account_role")
    return None

