from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from app.auth.services import AuthService
from app.auth.models import User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

# Define the OAuth2 scheme for Swagger UI - this creates the lock icon
oauth2_scheme = HTTPBearer()

async def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> str:
    """
    Extract JWT token from the Authorization header using FastAPI's security utilities
    
    Args:
        credentials: The credentials extracted by the HTTPBearer scheme
        
    Returns:
        str: The JWT token
    """
    return credentials.credentials


async def get_current_user(token: str = Depends(get_token_from_header)) -> User:
    """
    Get the current authenticated user based on the JWT token
    
    Args:
        token: JWT token extracted from Authorization header
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    return await AuthService.get_current_user(token)