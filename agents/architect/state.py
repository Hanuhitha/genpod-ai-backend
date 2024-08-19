"""Architect State

This module contains the ArchitectState class which is a TypedDict representing 
the state of the Architect agent. It also includes functions to manipulate the 
state.
"""

from typing_extensions import TypedDict
from typing_extensions import Annotated

from models.architect import RequirementsOverview
from models.models import Task

class ArchitectState(TypedDict): 
    """
    ArchitectState Class

    This class encapsulates the state of the Architect agent, providing a 
    snapshot of the ongoing project's status and progress. 

    Attributes:
        user_request (str): The original set of requirements provided by the user, 
        serving as the foundation for the project.

        user_requested_standards (str): The specific standards or protocols the user has 
        requested to be implemented in the project, which could include coding standards, 
        design patterns, or industry-specific standards.

        project_status (str): An enumerated value reflecting the project's current lifecycle 
        stage, providing real-time tracking of project progress.

        generated_project_path (str): The absolute path in the file system where the project 
        is being generated. This path is used to store all the project-related files and 
        directories.

        license_text (str): The text of the license provided by the user. This text outlines 
        the terms and conditions under which the project can be used, modified, and distributed.

        messages (list[tuple[str, str]]): A chronological list of tuples representing the 
        conversation history between the system, user, and AI. Each tuple contains a role 
        identifier (e.g., 'AI', 'tool', 'user', 'system') and the corresponding message.
        
        current_task (Task): The Task object currently in focus, representing the active task 
        that team members are working on.

        project_name (str): The name of the project.

        project_folder_structure (str): The organized layout of directories and subdirectories 
        that form the project's file system, adhering to best practices for project structure.

        requirements_overview (str): A comprehensive, well-structured document in markdown 
        format that outlines the project's requirements derived from the user's request. 
        This serves as a guide for the development process.

        tasks (list[Task]): A list of Task objects, each encapsulating a distinct unit of work 
        necessary for the project's completion. These tasks are meant to be carried out by the 
        entire team collectively.

        query_answered (bool): A boolean flag indicating whether the task has been answered
    """
    # @in 
    user_request: Annotated[
        str,
        "The original set of requirements provided by the user, serving as the "
        "foundation for the project."
    ]

    # @in
    user_requested_standards: Annotated[
        str,
        "The specific standards or protocols the user has requested to be implemented"
        " in the project, which could include coding standards, design patterns, or "
        "industry-specific standards."
    ]

    # @in
    project_status: Annotated[
        str,
        "An enumerated value reflecting the project's current lifecycle stage, providing "
        "real-time tracking of project progress."
    ]

    # @in
    generated_project_path: Annotated[
        str,
        "The absolute path in the file system where the project is being generated. "
        "This path is used to store all the project-related files and directories."
    ]
    
    # @in
    license_text: Annotated[
        str,
        "The text of the license provided by the user. This text outlines the terms and "
        "conditions under which the project can be used, modified, and distributed."
    ]

    # @inout
    messages: Annotated[
        list[tuple[str, str]], 
        "A chronological list of tuples representing the conversation history between the "
        "system, user, and AI. Each tuple contains a role identifier (e.g., 'AI', 'tool', "
        "'user', 'system') and the corresponding message."
    ]

    # @inout
    current_task: Annotated[
        Task,
        "The Task object currently in focus, representing the active task that team "
        "members are working on."
    ]

    # @out
    project_name: Annotated[
        str, 
        "The name of the project."
    ]

    # @out
    project_folder_structure: Annotated[
        str,
        "The organized layout of directories and subdirectories that form the project's "
        "file system, adhering to best practices for project structure."
    ]

    # @out
    requirements_overview: Annotated[
        RequirementsOverview, 
        "A comprehensive, well-structured document in markdown format that outlines "
        "the project's requirements derived from the user's request. This serves as a "
        "guide for the development process."
    ]

    # @out
    tasks: Annotated[
        list[Task],
        "A list of Task objects, each encapsulating a distinct unit of work necessary "
        "for the project's completion. These tasks are meant to be carried out by the "
        "entire team collectively."
    ]

    # @out
    query_answered: Annotated[
        bool,
        "A boolean flag indicating whether the task has been answered",
    ]