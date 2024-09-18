"""TestCoder State

Agent graph state
"""

from typing_extensions import Annotated, TypedDict

from agents.agent.state import State
from models.constants import ChatRoles
from models.models import PlannedTask, Task
from models.tests_generator_models import FunctionSkeleton


class TestCoderState(TypedDict):
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
    project_folder_strucutre: Annotated[
        str,
        State.in_field(
            "The organized layout of directories and subdirectories that form the project's "
            "file system, adhering to best practices for project structure."
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
    test_code: Annotated[
        str,
        State.out_field(
            "The complete, well-documented working unit test code that adheres to all standards "
            "requested with the programming language, framework user requested ",
        )
    ]

    # @out
    files_created: Annotated[
        list[str],
        State.out_field(
            "The absolute paths of file that were created for this project "
            "so far."
        )
    ]

    # @out
    infile_license_comments: Annotated[
        dict[str, str],
        State.out_field(
            "A list of multiline license comments for each type of file."
        )
    ]

    # @out
    functions_skeleton:Annotated[
        FunctionSkeleton,
        State.out_field(
            "The well detailed function skeleton for the functions that are in the code."
        )
    ]

    # @out
    commands_to_execute: Annotated[ 
        dict[str, str],
        State.out_field(
            "This field represents a dictionary of commands intended to be executed on a Linux terminal. Each key-value pair in the dictionary corresponds to an absolute path (the key) and a specific command (the value) to be executed at that path."
        )
    ]

    # @in
    work_package:Annotated[
        str,
        State.in_field(
            "This contains the work package that needs to be segregated"
        )
    ]