"""
CSV import/export service for bulk user operations.
Handles CSV file validation, row processing, and user creation.
"""
import csv
import io

from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.db.models import User, AccountRoleEnum, JobRoleEnum, StatusEnum
from app.core.security import get_password_hash



# Required CSV columns for user import
REQUIRED_COLUMNS = ["name", "email", "password"]
# Optional CSV columns
OPTIONAL_COLUMNS = ["role", "status", "account_role"]
# Maximum file size: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_csv_columns(headers: List[str]) -> Tuple[bool, List[str]]:
    # Strictly validate CSV file columns.
    # Requires exact required columns and rejects unknown columns.
    # Returns Tuple of (is_valid: bool, errors: List[str])

    errors = []
    headers_lower = [h.lower().strip() for h in headers if h and h.strip()]
    if not headers_lower:
        errors.append("CSV file has no headers")
        return False, errors
    
    # Check for duplicate headers
    if len(headers_lower) != len(set(headers_lower)):
        duplicates = [h for h in set(headers_lower) if headers_lower.count(h) > 1]
        errors.append(f"Duplicate column headers found: {', '.join(duplicates)}")
    
    # Check all required columns are present
    for required in REQUIRED_COLUMNS:
        if required not in headers_lower:
            errors.append(f"Missing required column: {required}")
    
    # Check for unknown/extra columns (strict validation)
    all_valid_columns = set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
    unknown_columns = [h for h in headers_lower if h not in all_valid_columns]
    if unknown_columns:
        errors.append(f"Unknown columns found: {', '.join(unknown_columns)}. Allowed columns: {', '.join(sorted(all_valid_columns))}")
    
    return len(errors) == 0, errors

def process_csv_row(row: Dict[str, str], row_number: int, db: Session) -> Tuple[bool, Dict]:
    # Process a single CSV row and create user if valid.            
    # Returns (success: bool, result: dict with user_id or errors)

    errors = []
    
    # Validate required fieldsname, email, password
    name = row.get("name", "").strip()
    email = row.get("email", "").strip().lower()
    password = row.get("password", "").strip()
    
    # Validate name (2-100 characters)
    if not name or len(name) < 2 or len(name) > 100:
        errors.append("Name must be 2-100 characters")
    
    # Validate email format and uniqueness
    if not email:
        errors.append("Email is required")
    else:
        # Strict email format validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")
        elif len(email) > 254:
            errors.append("Email address is too long (max 254 characters)")
        else:
            # Check email uniqueness at DB level
            if db.query(User).filter(User.email == email).first():
                errors.append("Email already registered")
    
    # Validate password
    if not password:
        errors.append("Password is required")
    elif len(password) < 1:
        errors.append("Password cannot be empty")
    elif len(password) > 500:
        errors.append("Password is too long (max 500 characters)")
    elif password.strip() != password:
        errors.append("Password cannot have leading or trailing whitespace")
    
    # Validate optional fields
    role = row.get("role", "").strip().lower()
    if role and role not in ["manager", "developer"]:
        errors.append(f"Invalid role: {role}. Must be 'manager' or 'developer'")
    
    status = row.get("status", "active").strip().lower()
    if status and status not in ["active", "inactive"]:
        errors.append(f"Invalid status: {status}. Must be 'active' or 'inactive'")
    
    account_role = row.get("account_role", "end_user").strip().lower()
    if account_role and account_role not in ["admin", "corporate_admin", "end_user"]:
        errors.append(f"Invalid account_role: {account_role}")
    
    if errors:
        return False, {"row": row_number, "errors": errors}
    
    # Create user
    try:
        new_user = User(
            name=name,
            email=email,
            password=get_password_hash(password),
            role=JobRoleEnum(role) if role else None,
            status=StatusEnum(status) if status else StatusEnum.active,
            account_role=AccountRoleEnum(account_role) if account_role else AccountRoleEnum.end_user
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return True, {"row": row_number, "user_id": str(new_user.id)}
    except Exception as e:
        db.rollback()
        # Check for unique constraint violation
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, {"row": row_number, "errors": ["Email already registered (database constraint)"]}
        return False, {"row": row_number, "errors": [f"Database error: {str(e)}"]}

def process_csv_upload(file_content: bytes, db: Session) -> Dict:
    # Process CSV file upload for bulk user creation.   
    # Validates file size, format, columns, and processes each row.
    # Returns Dictionary with total_rows, users_created, and errors list

    # Check file size limit
    file_size = len(file_content)
    if file_size > MAX_FILE_SIZE:
        return {
            "total_rows": 0,
            "users_created": 0,
            "errors": [{"row": 0, "errors": [f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit"]}]
        }
    
    # Parse CSV file
    try:
        text_content = file_content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(text_content))
        headers = csv_reader.fieldnames or []
    except Exception as e:
        return {
            "total_rows": 0,
            "users_created": 0,
            "errors": [{"row": 0, "errors": [f"Invalid CSV format: {str(e)}"]}]
        }
    
    # Validate required columns exist
    is_valid, column_errors = validate_csv_columns(headers)
    if not is_valid:
        return {
            "total_rows": 0,
            "users_created": 0,
            "errors": [{"row": 0, "errors": column_errors}]
        }
    
    # Process each row individually
    total_rows = 0
    users_created = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (row 1 is header)
        total_rows += 1
        # Normalize column names (case-insensitive)
        normalized_row = {k.lower().strip(): v for k, v in row.items()}
        success, result = process_csv_row(normalized_row, row_num, db)
        
        if success:
            users_created += 1
        else:
            errors.append(result)
    return {
        "total_rows": total_rows,
        "users_created": users_created,
        "errors": errors
    }

def export_users_to_csv(
    users: List[User],
    filters: Dict = None
) -> str:
    # Export list of users to CSV format.
    # Returns CSV formatted string with user data
    output = io.StringIO()
    
    # Define CSV column headers
    fieldnames = ["id", "name", "email", "role", "status", "account_role", "created_at", "updated_at"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write each user as a CSV row
    for user in users:
        writer.writerow({
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value if user.role else "",
            "status": user.status.value if user.status else "",
            "account_role": user.account_role.value if user.account_role else "",
            "created_at": user.created_at.isoformat() if user.created_at else "",
            "updated_at": user.updated_at.isoformat() if user.updated_at else ""
        })
    
    return output.getvalue()

