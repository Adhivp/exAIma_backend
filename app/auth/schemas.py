from pydantic import BaseModel, Field, validator
from typing import Optional
import re


class UserBase(BaseModel):
    username: str = Field(..., description="Unique username for the user")
    email: str = Field(..., description="Email address of the user")
    full_name: str = Field(..., description="Full name of the user")
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email format")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username for login")
    password: str = Field(..., description="User password")


class UserResponse(UserBase):
    id: str = Field(..., description="Unique user identifier")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe"
            }
        }
    }


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Type of token")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }


class ErrorResponse(BaseModel):
    detail: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Invalid credentials"
            }
        }
    }