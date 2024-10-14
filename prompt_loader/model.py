
from pydantic import BaseModel
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class PartialVariable(BaseModel):
    class_: str = Field(..., alias='class')
    pydantic_object: str


class PromptTemplateModel(BaseModel):
    template: str
    input_variables: List[str]
    partial_variables: str


class UserPromptTemplateModel(BaseModel):
    user_template: str
    user_input_variables: List[str]


class Prompts(BaseModel):
    prompt_generation_prompt: PromptTemplateModel
    decision_agent_prompt: PromptTemplateModel


# class User_Prompts(BaseModel):
#     user_prompt = UserPromptTemplateModel


# class Config(BaseModel):
#     system_prompts: Prompts
#     user_prompts: User_Prompts
