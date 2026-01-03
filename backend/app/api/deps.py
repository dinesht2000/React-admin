
# Dependencies for FastAPI endpoints.
# Includes database session management and authentication dependencies.

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import get_role_from_token, decode_token
from app.core.rbac import require_role

def get_db():

    # Database session dependency.
    # Yields a database session and ensures it's closed after use.

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_role(authorization: Optional[str] = Header(None)) -> str:

    # Extract token from request and resolve account role using JWT

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    # Extract token from "Bearer <token>" or just "<token>" format
    if authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    else:
        token = authorization
    
    # Decode and validate JWT token signature and expiration
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    role = get_role_from_token(token)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has no associated role"
        )
    
    return role

def require_roles(required_roles: List[str]):

    # Dependency factory to check if user has required roles

    def role_checker(current_role: str = Depends(get_current_role)) -> str:
        require_role(current_role, required_roles)
        return current_role
    return role_checker

