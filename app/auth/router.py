from fastapi import APIRouter, HTTPException, status, Security
from app.auth.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.auth.services import AuthService
from app.auth.dependencies import get_current_user, get_token_from_header
from app.auth.models import User
from typing import Dict

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    return await AuthService.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login to get an access token"""
    return await AuthService.login_user(
        username=user_data.username,
        password=user_data.password
    )

# Protected routes using Security to trigger the lock icon in Swagger UI
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(token: str = Security(get_token_from_header)):
    """Logout and invalidate the current token"""
    return await AuthService.logout_user(token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Security(get_current_user)):
    """Get current user information"""
    return current_user