from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from app.auth.services import AuthService
from app.auth.models import User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from app.config import supabase

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


async def verify_exam_access(
    exam_id: str,
    current_user: User = Depends(get_current_user)
) -> bool:
    """
    Verify that the current user has access to view the specified exam history
    
    Args:
        exam_id: The ID of the exam to check access for
        current_user: The authenticated user
        
    Returns:
        bool: True if access is granted
        
    Raises:
        HTTPException: If the user does not have access to this exam's history
    """
    try:
        # Try to query the exam results for this user and exam
        result = supabase.table("user_exam_results").select("*").eq("exam_id", exam_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            # If no results, user hasn't taken this exam
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You haven't taken this exam yet"
            )
        
        return True
    except Exception as e:
        # Check if this is a table not found error
        if hasattr(e, 'message') and "relation" in str(e) and "does not exist" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam history feature is not available yet"
            )
        # For other errors, re-raise the exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying exam access: {str(e)}"
        )