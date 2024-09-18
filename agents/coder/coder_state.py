"""Coder State

Agent graph state
"""
from typing_extensions import Annotated, TypedDict

from agents.agent.state import State
from models.coder_models import CodeGenerationPlan
from models.constants import ChatRoles
from models.models import PlannedTask, Task


class CoderState(TypedDict):
    """
    """

    # @in 
    project_name: Annotated[
        str, 
        State.in_field(
            "The name of the project."
        )
    ]

    # @in 
    requirements_document: Annotated[
        str, 
        State.in_field(
            "A comprehensive, well-structured document in markdown format that outlines "
            "the project's requirements derived from the user's request. This serves as a "
            "guide for the development process."
        )
    ]

    # @in
    project_path: Annotated[
        str,
        State.in_field(
            "The absolute path in the file system where the project is being generated. "
            "This path is used to store all the project-related files and directories."
        )
    ]

    # @in
    license_url: Annotated[
        str,
        State.in_field()
    ]

    # @in
    license_text: Annotated[
        str, 
        State.in_field()
    ]

    # @in
    functions_skeleton:Annotated[
        dict,
        State.in_field(
            "The well detailed function skeleton for the functions that are in the code."
        )
    ]

    # @in
    test_code: Annotated[
        dict, 
        State.in_field(
            "The complete, well-documented working unit test code that adheres to all standards "
            "requested with the programming language, framework user requested "
        )
    ]

    # @inout
    current_task: Annotated[
        Task,
        State.inout_field(
            "The Task object currently in focus, representing the active task that team "
            "members are working on."
        )
    ]
    
    # @inout
    current_planned_task: Annotated[
        PlannedTask,
        State.inout_field(
            "The PlannedTask object currently in focus, representing the active task"
            "that coder need to work on."
        )
    ]
    
    # @inout
    messages: Annotated[
        list[tuple[ChatRoles, str]], 
        State.inout_field(
            "A chronological list of tuples representing the conversation history between the "
            "system, user, and AI. Each tuple contains a role identifier (e.g., 'AI', 'tool', "
            "'user', 'system') and the corresponding message."
        )
    ]

    # @out
    code_generation_plan_list: Annotated[
        CodeGenerationPlan,
        State.out_field()
    ]
