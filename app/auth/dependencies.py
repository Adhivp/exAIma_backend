from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from app.auth.services import AuthService
from app.auth.models import User


async def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract JWT token from the Authorization header
    
    Args:
        authorization: Authorization header value
        
    Returns:
        str: The JWT token
        
    Raises:
        HTTPException: If authorization header is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    scheme, _, token = authorization.partition(" ")
    
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    return token


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