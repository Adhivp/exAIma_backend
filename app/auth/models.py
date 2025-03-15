from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime


class User:
    """
    User model that maps to the users table in Supabase
    """
    def __init__(
        self,
        id: str,
        username: str,
        email: str,
        full_name: str,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.id = id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.created_at = created_at
        self.updated_at = updated_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        Create a User instance from a dictionary
        """
        return cls(
            id=data.get("id"),
            username=data.get("username"),
            email=data.get("email"),
            full_name=data.get("full_name"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User instance to dictionary
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }