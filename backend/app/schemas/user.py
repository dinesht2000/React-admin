from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
import uuid
from enum import Enum
import re

class AccountRoleEnum(str, Enum):
    admin = "admin"
    corporate_admin = "corporate_admin"
    end_user = "end_user"

class JobRoleEnum(str, Enum):
    manager = "manager"
    developer = "developer"

class StatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"

class UserCreate(BaseModel):
    # Schema for creating a new user with strict validation
    name: str = Field(..., min_length=2, max_length=100, description="User name (2-100 characters)")
    email: EmailStr = Field(..., description="User email address (must be unique)")
    password: str = Field(..., min_length=1, max_length=500, description="User password (will be hashed)")
    role: Optional[JobRoleEnum] = Field(None, description="Job role (manager, developer)")
    status: Optional[StatusEnum] = Field(StatusEnum.active, description="User status (active, inactive)")
    account_role: Optional[AccountRoleEnum] = Field(AccountRoleEnum.end_user, description="Account role (admin, corporate_admin, end_user)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        # Trim whitespace and validate name format
        if not v:
            raise ValueError("Name is required")
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must not exceed 100 characters")
        # Reject names with only whitespace or special characters
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', v):
            raise ValueError("Name contains invalid characters")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Additional email validation beyond EmailStr
        if not v:
            raise ValueError("Email is required")
        v = v.strip().lower()
        # Additional email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        # Reject emails that are too long
        if len(v) > 254:  # RFC 5321 limit
            raise ValueError("Email address is too long")
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Validate password strength
        if not v:
            raise ValueError("Password is required")
        if len(v) < 1:
            raise ValueError("Password cannot be empty")
        if len(v) > 500:
            raise ValueError("Password is too long")
        # Reject passwords with only whitespace
        if v.strip() != v:
            raise ValueError("Password cannot have leading or trailing whitespace")
        return v

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: Optional[str] = None
    status: str
    account_role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    # Schema for updating user - all fields optional with strict validation
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="User name (2-100 characters)")
    email: Optional[EmailStr] = Field(None, description="User email address")
    password: Optional[str] = Field(None, min_length=1, max_length=500, description="User password (will be hashed if provided)")
    role: Optional[JobRoleEnum] = Field(None, description="Job role (manager, developer)")
    status: Optional[StatusEnum] = Field(None, description="User status (active, inactive)")
    account_role: Optional[AccountRoleEnum] = Field(None, description="Account role (admin, corporate_admin, end_user)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        # Trim whitespace and validate name format if provided
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must not exceed 100 characters")
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', v):
            raise ValueError("Name contains invalid characters")
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        # Additional email validation if provided
        if v is None:
            return v
        v = v.strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        if len(v) > 254:
            raise ValueError("Email address is too long")
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Validate password if provided
        if v is None:
            return v
        if len(v) < 1:
            raise ValueError("Password cannot be empty")
        if len(v) > 500:
            raise ValueError("Password is too long")
        if v.strip() != v:
            raise ValueError("Password cannot have leading or trailing whitespace")
        return v

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int

class CSVUploadError(BaseModel):
    row: int
    errors: list[str]

class CSVUploadResponse(BaseModel):
    total_rows: int
    users_created: int
    errors: list[CSVUploadError]

