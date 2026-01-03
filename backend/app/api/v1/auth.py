from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import timedelta
from app.api.deps import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import ACCESS_TOKEN_EXPIRE_HOURS

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):

    #User login endpoint.
    #Validates email and password, returns JWT token with account role.
    
    # Find user by email
    user = db.query(User).filter(User.email == credentials.username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password against stored hash
    if not user.password or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    

    if user.status and user.status.value == "inactive":
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Create JWT token with user ID and account role
    account_role = user.account_role.value if user.account_role else "end_user"
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    token = create_access_token(
        data={"sub": str(user.id), "account_role": account_role},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(token=token, account_role=account_role)

