from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Define a request model for the demo endpoint
class DemoRequest(BaseModel):
    name: str
    items: List[str]
    description: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up exAIma_backend...")
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

@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Hello welcome to exAIma_backend"}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "healthy"}

@app.post("/demo")
async def demo_post(request: DemoRequest) -> Dict[str, Any]:
    """
    Demo POST endpoint that accepts JSON data and returns a response.
    
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
        "item_count": len(request.items)
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)