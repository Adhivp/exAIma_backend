from fastapi import APIRouter, Depends, HTTPException, status, Header, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Dict, Any, Optional, Annotated
from app.auth.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, ErrorResponse
from app.auth.services import AuthService
from app.auth.dependencies import get_current_user, get_token_from_header
from app.auth.models import User

# Set the correct tokenUrl with the full path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}
    }
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user with username, email, password, and full name"
)
async def register(user_data: UserCreate) -> Dict[str, Any]:
    """
    Register a new user in the system.
    
    - **username**: Unique username for the user
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)
    - **full_name**: User's full name
    
    Returns the created user information (without password).
    """
    return await AuthService.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Login with username and password to get access token"
)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Dict[str, Any]:
    """
    Authenticate a user and return an access token.
    
    - **username**: User's username
    - **password**: User's password
    
    Returns an access token that doesn't expire unless explicitly logged out.
    """
    return await AuthService.login_user(username=form_data.username, password=form_data.password)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout and invalidate the current access token",
    responses={401: {"model": ErrorResponse}}
)
async def logout(
    current_user: User = Security(get_current_user, scopes=[]),
    token: str = Depends(get_token_from_header)
) -> Dict[str, str]:
    """
    Logout a user by invalidating their access token.
    
    Requires authentication via Bearer token in the Authorization header.
    """
    return await AuthService.logout_user(token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user",
    responses={401: {"model": ErrorResponse}}
)
async def get_me(
    current_user: User = Security(get_current_user, scopes=[])
) -> Dict[str, Any]:
    """
    Get information about the currently authenticated user.
    
    Requires authentication via Bearer token in the Authorization header.
    """
    return current_user