# fast_api/main.py


from ast import List
import sqlite3
from venv import logger
from fastapi import FastAPI, HTTPException
from configs.database import get_client_local_db_file_path
from database.database import Database


from fast_api.models import LLMResponse, Metadata, ProjectInput, UserResponse
from fastapi.middleware.cors import CORSMiddleware
# from .routes import router


app = FastAPI(title="LLM Agent API", version="1.0.0")

user_project_details = []

enhanced_input = ""

additonal_input = []
request_id = 0
response_id = 0
count = 0
meta_data = []

DATABASE_PATH = get_client_local_db_file_path()
db = Database(DATABASE_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[" all "],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/app")
async def root():
    return {"message": "Hello World"}


@app.post("/metadata")
async def metadata(input: Metadata):
    try:
        meta_data.append(input)
        metadata = db.metadata_table.insert(
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
            system_process_id=input.system_process_id
        )
        logger.info("Metadata has been created!", metadata)

        return input

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}")


@app.post("/project_info")
async def start_conversation(input: ProjectInput):
    try:
        user_project_details.append(input)
        conversation = db.conversation_table.insert(
            request_id=input.request_id,
            conversation_id=1,
            user_input_prompt_message=input.user_input_prompt_message,
        )
        logger.info("Project Input has been created!", conversation)

        return input

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}")


@app.post("/additional_input")
async def post_additional_input(input: ProjectInput):
    try:
        additonal_input.append(input)
        conversation = db.conversation_table.insert(
            request_id=input.request_id,
            # input.response_id,
            conversation_id=1,
            user_input_prompt_message=input.user_input_prompt_message,
            # input.llm_output_prompt_message_response
        )
        logger.info("Project Input has been created!", conversation)

        return input

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}")


@app.get("/project_info", response_model=ProjectInput)
async def get_project_info():
    try:
        return user_project_details[-1]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving project info: {str(e)}"
        )


@app.get("/project_info_all", response_model=ProjectInput)
async def get_project_info():
    try:
        return user_project_details
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving project info: {str(e)}"
        )


@app.post("/enhanced_input", response_model=LLMResponse)
async def post_enhanced_input(input: LLMResponse):
    try:
        enhanced_input = input.llm_output_prompt_message_response
        response_id = input.response_id
        enhanced_conversation = db.conversation_table.insert(
            input.response_id,
            llm_output_prompt_message_response=input.llm_output_prompt_message_response
        )
        logger.info("Project Input has been created!", enhanced_conversation)

        return enhanced_input

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}")


@app.get("/product_info_all")
async def get_all_products():
    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM conversation")
        conversation = cursor.fetchall()

        if not conversation:
            raise HTTPException(
                status_code=404, detail="No conversation found")

        return conversation  # Convert rows to dicts
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching conversation: {str(e)}")
    finally:
        cursor.close()


@app.get("/product/{request_id}")
async def get_product_by_id(request_id: str):
    try:
        cursor = db.connection.cursor()
        cursor.execute(
            "SELECT * FROM conversation WHERE id = ?", (request_id,))
        conversation = cursor.fetchall()

        if not conversation:
            raise HTTPException(
                status_code=404, detail=f"conversation with ID {request_id} not found")

        return conversation
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching product: {str(e)}")
    finally:
        cursor.close()


@app.put("/update_conversation/{request_id}")
async def update_conversation(request_id: str, update_data: LLMResponse):
    try:
        cursor = db.connection.cursor()
        cursor.execute(f"""
            SELECT * FROM conversation 
            WHERE request_id = ? AND response_id IS NOT NULL
        """, (request_id,))
        record = cursor.fetchone()

        if record:
            cursor.execute(f"""
                UPDATE conversation
                SET response_id = ?, 
                    llm_output_prompt_message_response = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE request_id = ? AND response_id IS NOT NULL
            """, (
                update_data.response_id,
                update_data.llm_output_prompt_message_response,
                request_id
            ))
            db.connection.commit()
            logger.info(
                f"Record with request_id {request_id} updated successfully.")
            return record
        else:
            raise HTTPException(status_code=404,
                                detail=f"No matching record found with request_id {request_id} and response_id IS NOT NULL")

    except sqlite3.Error as e:
        logger.error(f"Error updating record: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error updating record: {str(e)}")

    finally:
        if cursor:
            cursor.close()


@app.get("/enhanced_input", response_model=LLMResponse)
async def get_enhanced_input():
    try:
        return enhanced_input

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting conversation: {str(e)}")


@app.get("/additional_input", response_model=UserResponse)
async def get_additional_input():
    try:
        return additonal_input[-1]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving project info: {str(e)}"
        )
