

from openai import BaseModel


class Conversation(BaseModel):
    request_id: str
    response_id: str
    user_input_prompt_message: str
    llm_output_prompt_message_response: str
    conversation_id: str


class Metadata(BaseModel):
    user_id: int
    session_id: int
    organisation_id: int
    project_id: int
    application_id: int
    user_email: str
    project_input: str
    usergitid: str
    task_id: int
    agent_name: str
    agent_id: str
    thread_id: str
    system_process_id: int


class LLMResponse(BaseModel):
    llm_output_prompt_message_response: str
    response_id: int


class UserResponse(BaseModel):
    response: str


class ProjectInput(BaseModel):
    user_input_prompt_message: str
    request_id: int
