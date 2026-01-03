from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    # Login request schema - validates user credentials
    username: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

class LoginResponse(BaseModel):
    # Login response schema - returns JWT token and user role
    token: str = Field(..., description="JWT access token")
    account_role: str = Field(..., description="User account role (admin, corporate_admin, end_user)")

