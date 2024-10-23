# fast_api/main.py

import asyncio
from typing import List
from ast import List
from datetime import datetime
import sqlite3
from venv import logger
from fastapi import FastAPI, HTTPException
from agents.prompt_agent.prompt_agent import PromptAgent
from configs.database import get_client_local_db_file_path
from configs.project_config import LLMConfig
from database.database import Database
from database.tables.conversation import Conversation
from fastapi.middleware.cors import CORSMiddleware

from fast_api.prompt_agent_fast_api.models import LLMResponse, Metadata, ProjectInput, UserResponse
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="LLM Agent API", version="1.0.0")

user_project_details = []

enhanced_input = ""
active_connections = {}
additonal_input = []
request_id = 0
response_id = 0
count = 0
meta_data = []

prompt_agent = PromptAgent(LLMConfig, WebSocket)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_PATH = get_client_local_db_file_path()
db = Database(DATABASE_PATH)
db.setup_db()


def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@app.get("/app")
async def root():
    return {"message": "Hello World"}


@app.get("/applications")
def get_all_conversations(db: Session = Depends(get_db)):
    """
    Query all conversations using SQLAlchemy ORM.
    """
    conversations = db.query(Conversation).all()
    return {"conversations": conversations}


@app.post("/metadata")
async def metadata(input: Metadata, db: Session = Depends(get_db)):
    try:
        new_metadata = Metadata(
            user_id=input.user_id,
            session_id=input.session_id,
            organisation_id=input.organisation_id,
            project_id=input.project_id,
            application_id=input.application_id,
            user_email=input.user_email,
            project_input=input.project_input,
            usergitid=input.usergitid,
            task_id=input.task_id,
            agent_name=input.agent_name,
            agent_id=input.agent_id,
            thread_id=input.thread_id,
            system_process_id=input.system_process_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_metadata)
        db.commit()
        db.refresh(new_metadata)

        logger.info("Metadata has been created!", new_metadata)

        return new_metadata

    except Exception as e:
        logger.error(f"Error creating metadata: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error creating metadata: {str(e)}"
        )


@app.post("/project_info")
async def start_conversation(input: ProjectInput, db: Session = Depends(get_db)):
    try:
        new_conversation = Conversation(
            request_id=input.request_id,
            conversation_id=1,
            user_input_prompt_message=input.user_input_prompt_message,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)

        logger.info("Project Input has been created!", new_conversation)
        return new_conversation

    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}"
        )


@app.post("/additional_input")
async def post_additional_input(input: ProjectInput, db: Session = Depends(get_db)):
    try:
        new_conversation = Conversation(
            request_id=input.request_id,
            conversation_id=1,
            user_input_prompt_message=input.user_input_prompt_message,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)

        logger.info("Project Input has been created!", new_conversation)

        return new_conversation

    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}"
        )


@app.get("/project_info", response_model=ProjectInput)
async def get_project_info(db: Session = Depends(get_db)):
    try:
        project_info = db.query(Conversation).order_by(
            Conversation.id.desc()).first()

        if not project_info:
            raise HTTPException(
                status_code=404, detail="No project info found"
            )

        return project_info

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving project info: {str(e)}"
        )


@app.post("/enhanced_input", response_model=LLMResponse)
async def post_enhanced_input(input: LLMResponse, db: Session = Depends(get_db)):
    try:
        enhanced_conversation = Conversation(
            response_id=input.response_id,
            llm_output_prompt_message_response=input.llm_output_prompt_message_response,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(enhanced_conversation)
        db.commit()
        db.refresh(enhanced_conversation)

        logger.info("Project Input has been created!", enhanced_conversation)

        return enhanced_conversation

    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}"
        )


@app.get("/product_info_all")
async def get_all_products(db: Session = Depends(get_db)):
    try:
        conversations = db.query(Conversation).all()

        if not conversations:
            raise HTTPException(
                status_code=404, detail="No conversation found"
            )

        return conversations

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching conversation: {str(e)}"
        )


@app.get("/product/{request_id}")
async def get_product_by_id(request_id: int, db: Session = Depends(get_db)):
    try:
        conversation = db.query(Conversation).filter(
            Conversation.id == request_id).first()

        if not conversation:
            raise HTTPException(
                status_code=404, detail=f"Conversation with ID {request_id} not found"
            )

        return conversation

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching conversation: {str(e)}"
        )


@app.put("/update_conversation/{request_id}")
async def update_conversation(request_id: str, update_data: LLMResponse, db: Session = Depends(get_db)):
    try:
        conversation = db.query(Conversation).filter(
            Conversation.request_id == request_id,
        ).first()

        if conversation:
            conversation.response_id = update_data.response_id
            conversation.llm_output_prompt_message_response = update_data.llm_output_prompt_message_response
            conversation.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(conversation)

            logger.info(
                f"Record with request_id {request_id} updated successfully.")
            return conversation
        else:
            raise HTTPException(
                status_code=404, detail=f"No matching record found with request_id {request_id} and response_id IS NOT NULL")

    except Exception as e:
        logger.error(f"Error updating record: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating record: {str(e)}")


@app.get("/enhanced_input", response_model=LLMResponse)
async def get_enhanced_input(db: Session = Depends(get_db)):
    try:
        enhanced_input = db.query(Conversation).filter(Conversation.llm_output_prompt_message_response.isnot(
            None)).order_by(Conversation.updated_at.desc()).first()

        if not enhanced_input:
            raise HTTPException(
                status_code=404, detail="No enhanced input found"
            )

        return enhanced_input

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching enhanced input: {str(e)}")


@app.get("/additional_input", response_model=UserResponse)
async def get_additional_input(db: Session = Depends(get_db)):
    try:
        additional_input = db.query(Conversation).order_by(
            Conversation.updated_at.desc()).first()

        if not additional_input:
            raise HTTPException(
                status_code=404, detail="No additional input found"
            )

        return additional_input

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving additional input: {str(e)}"
        )


@app.get("/enhanced_prompt/{request_id}", response_model=LLMResponse)
async def get_enhanced_prompt(request_id: int, db: Session = Depends(get_db)):
    max_retries = 300
    retry_interval = 3

    try:
        for _ in range(max_retries):
            conversation = db.query(Conversation).filter(
                Conversation.request_id == request_id).first()

            if conversation and conversation.llm_output_prompt_message_response:
                return conversation

            await asyncio.sleep(retry_interval)

        raise HTTPException(
            status_code=404, detail="Enhanced prompt response not found for the given request_id.")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving enhanced prompt: {str(e)}"
        )


@app.websocket("/ws/enhanced_prompt/{request_id}")
async def websocket_enhanced_prompt(websocket: WebSocket, request_id: int, db: Session = Depends(get_db)):
    await websocket.accept()

    try:
        max_retries = 300
        retry_interval = 3

        for _ in range(max_retries):
            conversation = db.query(Conversation).filter(
                Conversation.request_id == request_id).first()

            if conversation and conversation.llm_output_prompt_message_response:
                await websocket.send_json({
                    "status": "success",
                    "llm_response": conversation.llm_output_prompt_message_response
                })
                await websocket.close()
                return

            await asyncio.sleep(retry_interval)

        await websocket.send_json({
            "status": "error",
            "message": "Enhanced prompt not found."
        })
        await websocket.close()

    except WebSocketDisconnect:
        print(
            f"Client disconnected while waiting for enhanced prompt: {request_id}")


@app.websocket("/ws/conversation/{request_id}")
async def websocket_conversation(websocket: WebSocket, request_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    active_connections[request_id] = websocket
    try:
        while True:
            # Wait for messages from the CLI
            message = await websocket.receive_text()
            message_data = eval(message)

            # Store project input in the DB
            if "user_input_prompt_message" in message_data:
                project_input = message_data['user_input_prompt_message']
                new_conversation = Conversation(
                    request_id=request_id,
                    user_input_prompt_message=project_input,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_conversation)
                db.commit()

                await websocket.send_text(f"Project input received for Request ID {request_id}")

            # Handle additional input
            elif "additional_input" in message_data:
                additional_input = message_data['additional_input']
                conversation = Conversation(
                    request_id=request_id,
                    user_input_prompt_message=additional_input,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(conversation)
                db.commit()

                await websocket.send_text(f"Additional input received for Request ID {request_id}")

    except WebSocketDisconnect:
        del active_connections[request_id]
        print(f"Client {request_id} disconnected.")


# @app.websocket("/ws/conversation/{request_id}")
# async def websocket_conversation(websocket: WebSocket, request_id: int, db: Session = Depends(get_db)):
#     await websocket.accept()
#     active_connections[request_id] = websocket
#     try:
#         while True:
#             # Step 1: Receive the input from the client (CLI)
#             message = await websocket.receive_text()
#             message_data = eval(message)

#             # Handle project input
#             if "user_input_prompt_message" in message_data:
#                 project_input = message_data['user_input_prompt_message']
#                 # Save the project input to the database
#                 new_conversation = Conversation(
#                     request_id=request_id,
#                     user_input_prompt_message=project_input,
#                     created_at=datetime.utcnow(),
#                     updated_at=datetime.utcnow()
#                 )
#                 db.add(new_conversation)
#                 db.commit()
#                 db.refresh(new_conversation)

#                 # Step 2: Process the input with the Prompt Agent
#                 refined_response = prompt_agent.chat_node({
#                     'original_user_input': project_input,
#                     'messages': [],
#                     'status': False,
#                     'request_id': request_id
#                 })

#                 # Step 3: Send the refined response back to the client
#                 await websocket.send_text(f"Refined Response: {refined_response['messages'][-1]}")

#             # Handle additional input
#             elif "additional_input" in message_data:
#                 additional_input = message_data['additional_input']
#                 new_conversation = Conversation(
#                     request_id=request_id,
#                     user_input_prompt_message=additional_input,
#                     created_at=datetime.utcnow(),
#                     updated_at=datetime.utcnow()
#                 )
#                 db.add(new_conversation)
#                 db.commit()
#                 db.refresh(new_conversation)

#                 # Process the additional input through the Prompt Agent
#                 refined_response = prompt_agent.chat_node({
#                     'original_user_input': additional_input,
#                     'messages': [],
#                     'status': False,
#                     'request_id': request_id
#                 })

#                 # Send the refined additional input response
#                 await websocket.send_text(f"Additional Input Refined: {refined_response['messages'][-1]}")

#     except WebSocketDisconnect:
#         del active_connections[request_id]
#         print(f"Client {request_id} disconnected.")
