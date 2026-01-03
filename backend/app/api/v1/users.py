import uuid

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.deps import get_db, get_current_role, require_roles
from app.db.models import User, AccountRoleEnum, JobRoleEnum, StatusEnum
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserListResponse, CSVUploadResponse
from app.services.csv_service import process_csv_upload, export_users_to_csv
from app.core.security import get_password_hash


router = APIRouter()

@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max 100)"),
    sort_field: Optional[str] = Query(None, description="Field to sort by (name, email, created_at, etc.)"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Sort order (asc or desc)"),
    role: Optional[str] = Query(None, description="Filter by job role (manager, developer)"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive)"),
    account_role: Optional[str] = Query(None, description="Filter by account role (admin, corporate_admin, end_user)"),
    search: Optional[str] = Query(None, description="Search in name and email"),
    db: Session = Depends(get_db),
    current_role: str = Depends(get_current_role)
):

    # List users with pagination, sorting, filtering, and search.
    # Requires authentication. Checks if user has required roles.


    query = db.query(User)
    
    # Filtering by job role
    if role:
        try:
            role_enum = JobRoleEnum(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role}. Must be 'manager' or 'developer'")
    
    # Filtering by status
    if status:
        try:
            status_enum = StatusEnum(status)
            query = query.filter(User.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Must be 'active' or 'inactive'")
    
    # Filtering by account role
    if account_role:
        try:
            account_role_enum = AccountRoleEnum(account_role)
            query = query.filter(User.account_role == account_role_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid account_role: {account_role}. Must be 'admin', 'corporate_admin', or 'end_user'")
    
    # Search (name or email)
    if search:
        search_filter = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Get total count before pagination
    total = query.count()
    
    # Sorting - validate sort field exists on User model
    if sort_field:
        sort_column = getattr(User, sort_field, None)
        if sort_column:
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            raise HTTPException(status_code=400, detail=f"Invalid sort_field: {sort_field}")
    else:
        # Default sort by created_at desc
        query = query.order_by(User.created_at.desc())
    
    # Pagination
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    
    return UserListResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_role: str = Depends(get_current_role)
):
    # Get user by ID - accessible to all authenticated users

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("", response_model=UserResponse)
async def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_role: str = Depends(require_roles(["admin"]))
):

    # Create a new user.
    # Only admin can create users.
    # Validates email uniqueness and hashes password.

    # Re-validate email uniqueness at DB level (never trust frontend)
    existing_user = db.query(User).filter(User.email == user.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user with hashed password
    try:
        new_user = User(
            name=user.name,  # Already validated and trimmed in schema
            email=user.email.lower().strip(),  # Normalize email
            password=get_password_hash(user.password),
            role=JobRoleEnum(user.role.value) if user.role else None,
            status=StatusEnum(user.status.value) if user.status else StatusEnum.active,
            account_role=AccountRoleEnum(user.account_role.value) if user.account_role else AccountRoleEnum.end_user
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        # Check if error is due to unique constraint violation (DB level)
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered (database constraint)")
        raise HTTPException(status_code=500, detail="Error creating user. Please try again.")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_role: str = Depends(get_current_role)
):

    # Update user information.
    # - Admin: Can update all fields
    # - Corporate Admin: Can update only job role
    # - End User: Cannot update

    # Find user by ID
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Admin can update all fields
    if current_role == "admin":
        if user_update.name is not None:
            user.name = user_update.name.strip() if user_update.name else user.name
        if user_update.email is not None:
            # Re-validate email uniqueness at DB level (never trust frontend)
            normalized_email = user_update.email.lower().strip()
            existing_user = db.query(User).filter(User.email == normalized_email, User.id != user_id).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            user.email = normalized_email
        if user_update.password is not None:
            user.password = get_password_hash(user_update.password)
        if user_update.role is not None:
            user.role = JobRoleEnum(user_update.role.value) if user_update.role else None
        if user_update.status is not None:
            user.status = StatusEnum(user_update.status.value)
        if user_update.account_role is not None:
            user.account_role = AccountRoleEnum(user_update.account_role.value)
    
    # Corporate Admin can only update job role
    elif current_role == "corporate_admin":
        if user_update.role is not None:
            user.role = JobRoleEnum(user_update.role.value) if user_update.role else None
        else:
            raise HTTPException(
                status_code=403, 
                detail="Corporate Admin can only update job role field"
            )
        # Reject attempts to update other fields
        if any([user_update.name, user_update.email, user_update.password, 
                user_update.status, user_update.account_role]):
            raise HTTPException(
                status_code=403,
                detail="Corporate Admin can only update job role field"
            )
    
    # End users cannot update
    else:
        raise HTTPException(status_code=403, detail="Insufficient permissions to update user")
    
    # Commit changes
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        # Check if error is due to unique constraint violation
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered (database constraint)")
        raise HTTPException(status_code=500, detail="Error updating user. Please try again.")

@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_role: str = Depends(require_roles(["admin"]))
):
    # Delete user - only admin can delete users

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting user. Please try again.")

@router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_role: str = Depends(require_roles(["admin"]))
):

    # Upload CSV file to bulk create users.
    # Admin only.
    # Validates file type, size, and required columns.
    # Returns detailed results with per-row errors.

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    # Validate file size before reading (prevent large file uploads)
    # Note: FastAPI's UploadFile doesn't expose size before reading,
    # but we check it in process_csv_upload after reading
    
    # Read file content with size limit
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Validate file size immediately
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    file_size = len(file_content)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit"
        )
    
    # Validate file is not empty
    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    # Process CSV upload
    result = process_csv_upload(file_content, db)
    return CSVUploadResponse(**result)

@router.get("/export-csv")
async def export_csv(
    role: Optional[str] = Query(None, description="Filter by job role (manager, developer)"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive)"),
    account_role: Optional[str] = Query(None, description="Filter by account role (admin, corporate_admin, end_user)"),
    search: Optional[str] = Query(None, description="Search in name and email"),
    sort_field: Optional[str] = Query(None, description="Field to sort by (name, email, created_at, etc.)"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db),
    current_role: str = Depends(require_roles(["admin"]))
):
    # Export users as CSV - Admin only. Applies same filters, search, and sorting as list API

    query = db.query(User)
    
    # Apply same filters as list API with validation
    if role:
        try:
            query = query.filter(User.role == JobRoleEnum(role))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    if status:
        try:
            query = query.filter(User.status == StatusEnum(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if account_role:
        try:
            query = query.filter(User.account_role == AccountRoleEnum(account_role))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid account_role: {account_role}")
    
    # Search (name or email)
    if search:
        search_filter = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Sorting
    if sort_field:
        sort_column = getattr(User, sort_field, None)
        if sort_column:
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
    else:
        # Default sort by created_at desc
        query = query.order_by(User.created_at.desc())
    
    # Get all users (no pagination for export)
    users = query.all() 
    
    # Generate CSV
    csv_content = export_users_to_csv(users)
    
    # Return CSV with proper headers for download
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users_export.csv"
        }
    )

