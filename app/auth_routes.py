"""
Authentication & Authorization API Routes
Provides secure REST endpoints for user signup, login, session validation,
and logout with PBKDF2-HMAC-SHA256 password hashing and SQLite persistence.
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import secrets
import sqlite3

from src.auth import register_user, authenticate_user, get_db_connection, get_user_by_username
from src.tracker import track_activity

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory token store for active sessions: token -> user_data
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}


class SignUpRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = ""
    tier: Optional[str] = "pro"


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)  # Can be username or email
    password: str = Field(..., min_length=1)



@router.post("/signup")
@router.post("/register")
async def signup(req: SignUpRequest):
    """Register a new user account with secure password hashing."""
    success, message = register_user(
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name or req.username,
        tier=req.tier or "pro"
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    user_data = get_user_by_username(req.username)
    if not user_data:
        user_data = {
            "username": req.username,
            "email": req.email,
            "full_name": req.full_name or req.username,
            "tier": req.tier or "pro",
        }

    # Generate session token
    token = secrets.token_hex(24)
    ACTIVE_SESSIONS[token] = user_data

    return {
        "status": "success",
        "message": "Account created successfully! Welcome to Market ML.",
        "user": user_data,
        "token": token
    }


@router.post("/login")
async def login(req: LoginRequest):
    """Authenticate existing user credentials."""
    success, message, user_data = authenticate_user(
        username_or_email=req.username,
        password=req.password
    )

    if not success or not user_data:
        raise HTTPException(status_code=401, detail=message)

    # Sanitize user dict (remove sensitive fields if any)
    user_info = {
        "id": user_data.get("id"),
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "full_name": user_data.get("full_name"),
        "tier": user_data.get("tier", "pro"),
        "created_at": user_data.get("created_at")
    }

    # Generate session token
    token = secrets.token_hex(24)
    ACTIVE_SESSIONS[token] = user_info

    return {
        "status": "success",
        "message": message,
        "user": user_info,
        "token": token
    }


@router.get("/me")
async def get_current_user(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
    username: Optional[str] = Query(None)
):
    """Validate current session token or fetch active user profile."""
    auth_token = token
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]

    if auth_token and auth_token in ACTIVE_SESSIONS:
        return {
            "status": "success",
            "authenticated": True,
            "user": ACTIVE_SESSIONS[auth_token]
        }

    # Fallback lookup by username if provided
    if username:
        user = get_user_by_username(username)
        if user:
            return {
                "status": "success",
                "authenticated": True,
                "user": user
            }

    raise HTTPException(status_code=401, detail="Session expired or invalid credentials")


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
):
    """Invalidate active session token."""
    auth_token = token
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.split(" ")[1]

    if auth_token and auth_token in ACTIVE_SESSIONS:
        user = ACTIVE_SESSIONS.pop(auth_token)
        track_activity(
            action="USER_LOGOUT",
            username=user.get("username", "guest"),
            details={"logout_status": "successful"}
        )

    return {
        "status": "success",
        "message": "Logged out successfully"
    }
