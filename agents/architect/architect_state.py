"""Architect State

This module contains the ArchitectState class which is a TypedDict representing 
the state of the Architect agent. It also includes functions to manipulate the 
state.
"""
from typing_extensions import Annotated, TypedDict

from agents.agent.state import State
from models.constants import ChatRoles
from models.models import RequirementsDocument, Task


class ArchitectState(TypedDict): 
    """
    ArchitectState Class

    This class encapsulates the state of the Architect agent, providing a 
    snapshot of the ongoing project's status and progress. 

    Attributes:
        original_user_input (str): The original set of requirements provided by the user, 
        serving as the foundation for the project.

        user_requested_standards (str): The specific standards or protocols the user has 
        requested to be implemented in the project, which could include coding standards, 
        design patterns, or industry-specific standards.

        project_status (str): An enumerated value reflecting the project's current lifecycle 
        stage, providing real-time tracking of project progress.

        project_path (str): The absolute path in the file system where the project 
        is being generated. This path is used to store all the project-related files and 
        directories.

        license_text (str): The text of the license provided by the user. This text outlines 
        the terms and conditions under which the project can be used, modified, and distributed.

        messages (list[tuple[ChatRoles, str]]): A chronological list of tuples representing the 
        conversation history between the system, user, and AI. Each tuple contains a role 
        identifier (e.g., 'AI', 'tool', 'user', 'system') and the corresponding message.
        
        current_task (Task): The Task object currently in focus, representing the active task 
        that team members are working on.

        project_name (str): The name of the project.

        project_folder_structure (str): The organized layout of directories and subdirectories 
        that form the project's file system, adhering to best practices for project structure.

        requirements_document (str): A comprehensive, well-structured document in markdown 
        format that outlines the project's requirements derived from the user's request. 
        This serves as a guide for the development process.

        tasks (list[Task]): A list of Task objects, each encapsulating a distinct unit of work 
        necessary for the project's completion. These tasks are meant to be carried out by the 
        entire team collectively.

        query_answered (bool): A boolean flag indicating whether the task has been answered
    """
    # @in 
    original_user_input: Annotated[
        str,
        State.in_field(
            "The original set of requirements provided by the user, serving as the "
            "foundation for the project."
        )
    ]

    # @in
    user_requested_standards: Annotated[
        str,
        State.in_field(
            "The specific standards or protocols the user has requested to be implemented"
            " in the project, which could include coding standards, design patterns, or "
            "industry-specific standards."
        )
    ]

    # @in
    project_status: Annotated[
        str,
        State.in_field(
            "An enumerated value reflecting the project's current lifecycle stage, providing "
            "real-time tracking of project progress."
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
    license_text: Annotated[
        str,
        State.in_field(
            "The text of the license provided by the user. This text outlines the terms and "
            "conditions under which the project can be used, modified, and distributed."
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

    # @inout
    current_task: Annotated[
        Task,
        State.inout_field(
            "The Task object currently in focus, representing the active task that team "
            "members are working on."
        )
    ]

    # @out
    project_name: Annotated[
        str, 
        State.out_field(
            "The name of the project."
        )
    ]

    # @out
    requirements_document: Annotated[
        RequirementsDocument, 
        State.out_field(
            "A comprehensive, well-structured document in markdown format that outlines "
            "the project's requirements derived from the user's request. This serves as a "
            "guide for the development process."
        )
    ]

    # @out
    tasks: Annotated[
        list[Task],
        State.out_field(
            "A list of Task objects, each encapsulating a distinct unit of work necessary "
            "for the project's completion. These tasks are meant to be carried out by the "
            "entire team collectively."
        )
    ]

    # @out
    query_answered: Annotated[
        bool,
        State.out_field(
            "A boolean flag indicating whether the task has been answered"
        )
    ]
