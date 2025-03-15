from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Import auth router correctly
from app.auth.router import router as auth_router
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.config import initialize_database

# Define a request model for the demo endpoint
class DemoRequest(BaseModel):
    name: str
    items: List[str]
    description: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up exAIma_backend...")
    # Initialize database during startup
    initialize_database()
    yield
    print("Shutting down exAIma_backend...")


app = FastAPI(
    title="exAIma Backend API",
    description="Backend API for exAIma application",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create public and protected routers
public_router = APIRouter(tags=["Public"])
protected_router = APIRouter(
    tags=["Protected"], 
    dependencies=[Depends(get_current_user)]
)

# Public endpoints
@public_router.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Hello welcome to exAIma_backend"}

@public_router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "healthy"}

# Protected endpoints
@protected_router.post("/demo")
async def demo_post(
    request: DemoRequest, 
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Demo POST endpoint that accepts JSON data and returns a response.
    Requires authentication.
    
    Example request body:
    {
        "name": "example",
        "items": ["item1", "item2"],
        "description": "This is a demo request"
    }
    """
    return {
        "message": f"Hello, {request.name}!",
        "received_items": request.items,
        "description": request.description,
        "item_count": len(request.items),
        "user": current_user.username
    }

# Include routers with appropriate prefixes
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(protected_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)