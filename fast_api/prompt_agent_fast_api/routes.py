# fast-api/routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.prompt_agent.prompt_agent import PromptAgent
from agents.prompt_agent.prompt_graph import PromptGraph
from agents.prompt_agent.prompt_state import PromptState
from configs.database import get_client_local_db_file_path
from database.database import Database
from configs.project_config import ProjectConfig
import os
from fast_api.prompt_agent_fast_api.models import ContinueConversationRequest, ConversationResponse, StartConversationRequest
from policies.pydantic_models.constants import ChatRoles

# Router object
router = APIRouter()

# Initialize necessary components
config = ProjectConfig()
prompt_config = config.agents_config[config.agents.prompt.agent_id]

DATABASE_PATH = get_client_local_db_file_path()
db = Database(DATABASE_PATH)
db.setup_db()

# Initialize the PromptGraph
prompt_engineer_graph = PromptGraph(
    prompt_config.llm, persistance_db_path=DATABASE_PATH)


@router.post("/start_conversation", response_model=ConversationResponse)
async def start_conversation(request: StartConversationRequest):
    try:

        initial_state = {
            'original_user_input': request.initial_input,
            'messages': [],
            'status': False
        }

        prompt_response = prompt_engineer_graph.app.stream(
            initial_state, {"configurable": {
                "thread_id": prompt_config.thread_id}}
        )

        for response in prompt_response:
            if "__end__" not in response:
                continue
            else:
                break

        return ConversationResponse(response=str(prompt_response), state_id=request.initial_input)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}")


@router.post("/continue_conversation", response_model=ConversationResponse)
async def continue_conversation(request: ContinueConversationRequest):
    try:
        # Retrieve current state
        current_state = prompt_engineer_graph.get_current_state()

        # Update state with user input
        current_state['messages'].append((ChatRoles.USER, request.user_input))

        # Stream the response again
        prompt_response = prompt_engineer_graph.app.stream(
            current_state, {"configurable": {
                "thread_id": prompt_config.thread_id}}
        )

        # Process the response
        for response in prompt_response:
            if "__end__" not in response:
                continue
            else:
                break

        # Save state and response
        return ConversationResponse(response=str(prompt_response), state_id=request.state_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error continuing conversation: {str(e)}")

# Optional: Endpoint to check the state of the conversation


@router.get("/conversation_state/{state_id}")
async def get_conversation_state(state_id: str):
    try:
        # You can implement state retrieval based on `state_id`
        current_state = prompt_engineer_graph.get_current_state()
        return current_state
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving state: {str(e)}")

# Optional: Endpoint to end a conversation


@router.post("/end_conversation")
async def end_conversation(state_id: str):
    try:
        # Clear state logic if necessary
        return {"message": "Conversation ended successfully", "state_id": state_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error ending conversation: {str(e)}")
