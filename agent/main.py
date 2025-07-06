import os
from contextlib import asynccontextmanager
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.science_chat import ScienceChatOrchestrator
from models.chat import ChatClient

# --- Models for API data validation ---
class UserInput(BaseModel):
    text: str

class ApiResponse(BaseModel):
    type: str
    content: str
    status: str = "success"

# --- Gloabl State and Lifespan Management ---
state: Dict[str, ScienceChatOrchestrator] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    print("--- Loading environment variables ---")
    load_dotenv(dotenv_path='models/.env')
    
    # Check for required environment variables
    required_vars = ["AGENT_API_SECRET_KEY", "API_BASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"FATAL: Missing environment variables: {', '.join(missing_vars)}")
        
    print("--- Initializing Shared Chat Client ---")
    chat_client = ChatClient()
    
    print("--- Initializing Science Chat Orchestrator ---")
    state["orchestrator"] = ScienceChatOrchestrator(
        chat_client=chat_client,
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000")
    )
    yield
    print("--- Shutting down ---")
    state.clear()


app = FastAPI(lifespan=lifespan)
auth_scheme = HTTPBearer()

# --- Authentication ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)):
    """Validates the Bearer token."""
    secret_key = os.getenv("AGENT_API_SECRET_KEY")
    if not secret_key or credentials.credentials != secret_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True # Token is valid


# --- API Endpoints ---
@app.get("/health", status_code=200)
async def health_check():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok"}


@app.post("/v1/chat/{chat_uuid}", response_model=ApiResponse)
async def chat_handler(
    chat_uuid: str,
    user_input: UserInput,
    authenticated: bool = Depends(get_current_user)
):
    """Handles incoming chat messages and commands for a specific chat session."""
    orchestrator = state["orchestrator"]
    response = await orchestrator.process_input(chat_uuid, user_input.text)
    return ApiResponse(**response)


@app.get("/v1/images/{chat_uuid}/{paper_hash}/{image_name}")
async def get_image(chat_uuid: str, paper_hash: str, image_name: str):
    """Serves a specific image from the cache."""
    orchestrator = state["orchestrator"]
    # Construct a safe path to the image
    image_path = orchestrator.papers_dir / paper_hash / "images" / image_name
    
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    # Prevent path traversal attacks by ensuring the path is within the cache dir
    try:
        image_path.resolve().relative_to(orchestrator.papers_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden")

    return FileResponse(image_path) 