from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from backend.dependencies import get_db, get_current_user, oauth2_scheme
from backend.models import User
from backend.schemas import LoginRequest, TokenResponse, UserResponse
from backend.core.security import verify_password, create_access_token, revoke_token
from backend.repositories.user_repository import UserRepository
from backend.core.audit import AuditLogger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, req_obj: Request, db: Session = Depends(get_db)):
    """Authenticate user with email and password, returning a JWT token."""
    client_ip = req_obj.client.host if req_obj.client else "unknown"
    user_agent = req_obj.headers.get("user-agent", "unknown")

    user_repo = UserRepository(db)
    user = user_repo.get_by_email(request.email)
    if not user or not verify_password(request.password, user.password_hash):
        AuditLogger.log(
            action="login_failed",
            resource="auth_login",
            client_ip=client_ip,
            user_agent=user_agent,
            result="failure",
            details={"email": request.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        AuditLogger.log(
            action="login_blocked_inactive",
            user_id=user.id,
            resource="auth_login",
            client_ip=client_ip,
            user_agent=user_agent,
            result="failure"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    access_token = create_access_token(data={"sub": user.uuid, "email": user.email, "role": user.role})
    AuditLogger.log(
        action="login_success",
        user_id=user.id,
        resource="auth_login",
        client_ip=client_ip,
        user_agent=user_agent,
        result="success"
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(token: Optional[str] = Depends(oauth2_scheme), current_user: User = Depends(get_current_user)):
    """Invalidates current JWT access token via token revocation."""
    if token:
        revoke_token(token)
        AuditLogger.log(
            action="logout_success",
            user_id=current_user.id,
            resource="auth_logout",
            result="success"
        )
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns profile and wallet status of current authenticated user."""
    return current_user
