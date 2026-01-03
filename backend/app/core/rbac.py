
# Role-Based Access Control (RBAC) utilities.
# Defines account roles and permission checking functions.

from typing import List
from fastapi import HTTPException, status

# Account roles available in the system
ACCOUNT_ROLES = ["admin", "corporate_admin", "end_user"]

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    "admin": 3,
    "corporate_admin": 2,
    "end_user": 1
}

def has_role(user_role: str, required_roles: List[str]) -> bool:

    # Check if user role is in the list of required roles.
    #Also checks role hierarchy - higher roles can access lower role permissions.
    
    if user_role in required_roles:
        return True
    
    # Check if user role has higher hierarchy than any required role
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    for required_role in required_roles:
        required_level = ROLE_HIERARCHY.get(required_role, 0)
        if user_level >= required_level:
            return True
    
    return False

def require_role(user_role: str, required_roles: List[str]):

    # Raise HTTPException if user doesn't have required role.
    # Checks both direct role match and role hierarchy.
    if not has_role(user_role, required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {required_roles}"
        )

