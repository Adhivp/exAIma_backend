from fastapi import HTTPException, status
from app.config import supabase, JWT_SECRET
from app.auth.models import User
import jwt
from datetime import datetime
from typing import Dict, Any
import uuid
import bcrypt


class AuthService:
    """
    Service for handling authentication operations
    """
    
    @staticmethod
    async def register_user(username: str, email: str, password: str, full_name: str) -> User:
        """
        Register a new user in the system with manual password hashing
        """
        try:
            # Check if username exists
            user_exists = supabase.table("users").select("*").eq("username", username).execute()
            if len(user_exists.data) > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
                
            # Check if email exists
            email_exists = supabase.table("users").select("*").eq("email", email).execute()
            if len(email_exists.data) > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            
            # Generate a unique user ID
            user_id = str(uuid.uuid4())
            
            # Hash password
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            # Prepare user data
            user_data = {
                "id": user_id,
                "username": username,
                "email": email,
                "full_name": full_name,
                "password_hash": hashed_password,  # Store the hashed password
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Insert user into database
            result = supabase.table("users").insert(user_data).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            # Return user without password hash
            user = User.from_dict(result.data[0])
            return user
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}"
            )
    
    @staticmethod
    async def login_user(username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user using manual password verification and generate JWT
        """
        try:
            # Get user by username
            user_result = supabase.table("users").select("*").eq("username", username).execute()
            
            if not user_result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
                
            user = user_result.data[0]
            
            # Verify password
            password_bytes = password.encode('utf-8')
            stored_hash = user.get("password_hash", "").encode('utf-8')
            
            if not bcrypt.checkpw(password_bytes, stored_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Generate token that doesn't expire
            payload = {
                "sub": user["id"],
                "username": user["username"],
                "email": user["email"],
                "iat": datetime.utcnow(),
                # No exp field means no expiration
            }
            
            token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
            
            # Store token in tokens table for logout capability
            token_data = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "token": token,
                "created_at": datetime.now().isoformat(),
                "is_revoked": False
            }
            
            supabase.table("tokens").insert(token_data).execute()
            
            return {
                "access_token": token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login error: {str(e)}"
            )
    
    @staticmethod
    async def logout_user(token: str) -> Dict[str, str]:
        """
        Logout a user by revoking their token
        """
        try:
            # Mark token as revoked in database
            update_result = supabase.table("tokens").update({"is_revoked": True}).eq("token", token).execute()
            
            if not update_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Token not found"
                )
            
            return {"detail": "Successfully logged out"}
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Logout error: {str(e)}"
            )
    
    @staticmethod
    async def get_current_user(token: str) -> User:
        """
        Get current user from token
        """
        try:
            # Check if token is revoked
            token_result = supabase.table("tokens").select("*").eq("token", token).eq("is_revoked", False).execute()
            
            if not token_result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked token"
                )
            
            # Decode token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database
            user_result = supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not user_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            return User.from_dict(user_result.data[0])
            
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication error: {str(e)}"
            )