from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from typing import List, Dict

# Import the agent and config we've already built
from app.my_agents import master_agent
from geminiConfig import gemini_config
from agents import Runner, set_tracing_disabled

# Disable tracing for the API
set_tracing_disabled(True)

# --- Step 1: Create our in-memory session storage ---
# This is a simple dictionary that will hold the history for each session.
# In a production application, this would be replaced with a real database like Redis.
SESSIONS: Dict[str, List[Dict[str, str]]] = {}

# Create the FastAPI app instance
app = FastAPI(
    title="HealthLine AI Assistant API",
    description="An API for interacting with the hospital booking agent.",
    version="1.1.0" # Version bump!
)

# --- Step 2: Update the request model to include a session_id ---
class ChatRequest(BaseModel):
    prompt: str
    session_id: str
    
# Create a simple root endpoint to confirm the server is running
@app.get("/")
def read_root():
    return {"status": "HealthLine AI Assistant API is running."}

# --- Step 3: Upgrade the chat endpoint to handle history ---
@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """
    Receives a user prompt and a session_id, and returns the agent's response,
    maintaining conversation history.
    """
    print(f"\nReceived prompt: '{request.prompt}' for session: {request.session_id}")
    
    # Get the history for this session, or create an empty list if it's a new session
    history = SESSIONS.get(request.session_id, [])
    
    # Append the user's new message to the history
    history.append({"role": "user", "content": request.prompt})

    try:
        # Run the agent with the FULL conversation history
        result = await Runner.run(
            starting_agent=master_agent,
            input=history,
            run_config=gemini_config,
        )

        # Append the agent's response to the history
        if result.final_output:
            history.append({"role": "assistant", "content": result.final_output})

        # Save the updated history back to our session store
        SESSIONS[request.session_id] = history
        
        print(f"Agent response: {result.final_output}")
        return {"response": result.final_output}
    
    except Exception as e:
        print(f"An error occurred in the agent runner: {e}")
        return {"error": "An internal error occurred. Please try again."}