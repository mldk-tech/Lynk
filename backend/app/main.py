from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

from .logic import process_user_message, get_initial_prompt
from .models import conversation_state # For managing state simply initially

app = FastAPI(title="Lynk Feature YAML Generator")

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserMessage(BaseModel):
    message: str
    # session_id: Optional[str] = None # For multi-user state

@app.on_event("startup")
async def startup_event():
    # Initialize or reset state if needed
    get_initial_prompt()

@app.post("/chat")
async def chat_endpoint(user_message: UserMessage) -> Dict[str, Any]:
    """
    Receives user message, processes it, and returns bot response.
    Response can be a question or the generated YAML.
    """
    # In a multi-user scenario, you'd use session_id to manage distinct states
    response_message, yaml_output = process_user_message(user_message.message, conversation_state)
    return {"reply": response_message, "yaml": yaml_output}

@app.post("/reset")
async def reset_chat_state() -> Dict[str, Any]:
    """
    Endpoint to reset the conversation state.
    """
    get_initial_prompt() # Resets state
    return {"reply": "Ok, let's start over. What type of Lynk feature would you like to create (Metric, First-Last, Formula, or Field)?", "yaml": None}

# Health check
@app.get("/")
def read_root():
    return {"message": "Lynk Feature YAML Generator Backend is running."}