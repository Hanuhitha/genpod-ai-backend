"""
This module defines the data model for the output of the Architect agent in 
the form of a Requirements Document.

The Requirements Document captures the details of the project requirements, 
such as the project name, a well-documented requirements document, a list of 
tasks derived from the requirements, the project folder structure to follow. 
Each of these details is represented as a field in the `RequirementsDoc` class.
"""

from typing_extensions import ClassVar

from pydantic import Field
from pydantic import BaseModel

from models.constants import Status
from models.models import Task

class TaskOutput(BaseModel):
    """
    This class represents the output of a task. It includes fields to indicate 
    whether additional information is needed to complete the task, the question 
    to ask for additional information, and the content of the requested information.
    """
    
    is_add_info_needed: bool = Field(
        description="Indicates whether additional information is needed to complete a task.",
        required=True
    )

    question_for_additional_info: str = Field(
        description="The question to ask when additional information is needed."
    )

    content: str = Field(
        description="The content of the requested information."
    )

class RequirementsOverview:

    project_details: str
    architecture: str
    folder_structure: str
    microservice_design: str
    task_description: str
    standards: str
    implementation_details: str
    license_details: str

class TasksList(BaseModel):
    """
    The TasksList class is a Pydantic model that represents a list of tasks for a project. 
    Each task in the list provides sufficient context and detailed information crucial for 
    the task completion process.
    """
    
    tasks: list[str] = Field(
        description="The list of tasks derived from the detailed requirements, "
        "each providing sufficient context with detailed information crucial for "
        "the task completion process", 
        required=True,
    )

    description: ClassVar[str] = "Schema representing a list of tasks derived from the project requirements."

class QueryResult(BaseModel):
    """
    This model represents the result of a query or question. It contains information 
    about whether an answer was found and what the answer is.
    """

    is_answer_found: bool = Field(
        description="Indicates if an answer was found or provided in response to the question",
        required=True
    )

    response_text: str = Field(
        description="The response provided to the user's question"
    )

    description: ClassVar[str] = "Schema representing the result of a query or question."