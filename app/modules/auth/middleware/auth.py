from fastapi import Depends, HTTPException, status
from typing import Optional
from ..services.auth_service import get_current_user

def authorize(required_role: Optional[str] = None):
    """
    Dependency factory for role-based access control.
    If required_role is None -> only validates token.
    If required_role is set -> validates token + checks user.role.name.
    """
    def role_checker(current_user=Depends(get_current_user)):
        if required_role:
            if not getattr(current_user, "role", None) or current_user.role.name != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access forbidden: requires {required_role} role",
                )
        return current_user

    return role_checker
