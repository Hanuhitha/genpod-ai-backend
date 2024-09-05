""" Graph State for PM Agent """
from typing import List

from typing_extensions import Annotated, TypedDict

from agents.agent.state import State
from models.constants import ChatRoles, PStatus
from models.models import (PlannedTask, PlannedTaskQueue, RequirementsDocument,
                           Task, TaskQueue)
from models.skeleton import FunctionSkeleton


class SupervisorState(TypedDict):
    """
    Represents the state of Project Manager to maintain the project level information and status.

    Attributes:
        original_user_input: User assigned task
        team_members: List of agents workflows that the Project Manager can invoke
        rag_retrieval: Whenever an agent needs any additional information a RAG Workflow is triggered to retrieve that information
        tasks: List of deliverables that needs to be completed to mark the project as complete
        current_task: Current task any agent is currently working on
        agents_status: What is the status of the agent that is currently working on the project
        messages: List of messages between Project Manager and other agents
    """

    # @in
    project_id: Annotated[
        int,
        State.in_field("The id of the project being generated.")
    ]

    # @out
    project_name: Annotated[
        str,
        State.out_field("The name of the project being generated.")
    ]

    # @out
    project_status: Annotated[
        PStatus,
        State.out_field("The status of the project being generated.")
    ]

    # @in
    microservice_id: Annotated[
        int, 
        State.in_field("The id of the microservice being generated.")
    ]

    # @out
    microservice_name: Annotated[
        str,
        State.out_field("The name of the microservice being generated.")
    ]

    # @in
    original_user_input: Annotated[
        str,
        State.in_field("The prompt given by user.")
    ]

    # @in
    project_path: Annotated[
        str,
        State.in_field("The path of the project where its being written.")
    ]

    # @in
    license_url: Annotated[
        str,
        State.in_field("The license url to the project, given by the user.")
    ]

    # @in
    license_text: Annotated[
        str,
        State.in_field("The license text for code base.")
    ]

    # @out
    tasks: Annotated[
        TaskQueue, 
        State.out_field("The tasks create while generating the project.")
    ]

    # @out
    current_task: Annotated[
        Task,
        State.out_field("The current task that team is working on.")
    ]

    # @out
    current_planned_task: Annotated[
        PlannedTask,
        State.out_field("The current planned task that team is working on.")
    ]

    # @out
    requirements_document: Annotated[
        RequirementsDocument,
        State.inout_field(
            "A comprehensive, well-structured document in markdown format that outlines "
            "the project's requirements derived from the user's request. This serves as a "
            "guide for the development process."
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
    human_feedback:  Annotated[
        list[tuple[str, str]], 
        State.inout_field(
            "A list human inputs given during human in the loop process"
        )
    ]

    # @out
    rag_cache_queries: Annotated[
        List[str],
        State.out_field("Queries generated for rag cache")
    ]

    # @out
    is_rag_query_answered : Annotated[
        bool,
        State.out_field("is query answered by rag agent.")
    ]

    # @out
    rag_retrieval: Annotated[
        str,
        State.out_field()
    ]

    # @out
    agents_status: Annotated[
        str,
        State.out_field()
    ]

    # @out
    planned_tasks: Annotated[
        PlannedTaskQueue, # This is list of work_packages created by the planner,
        State.out_field()
    ]

    # @out
    planned_task_map: Annotated[
        dict, # This is the a map of deliverables to work_packages
        State.out_field()
    ]

    # @out
    planned_task_requirements: Annotated[
        dict,  # This is the map of work_packages to json formatted requirements
        State.out_field()
    ]

    # @out - Architect 
    project_folder_strucutre: Annotated[
        str,
        State.in_field("The organized layout of directories and subdirectories that form the project's "
        "file system, adhering to best practices for project structure.")
    ]

    # @out
    code: Annotated[
        str, 
        State.out_field("The complete, well-documented working code that adheres to all standards "
        "requested with the programming language, framework user requested ")
    ]

    # @out
    files_created: Annotated[
        list[str], 
        State.out_field("The absolute paths of file that were created for this project "
        "so far.")
    ]

    # @out
    infile_license_comments: Annotated[
        dict[str, str],
        State.out_field("A list of multiline license comments for each type of file.")
    ]

    # @out
    commands_to_execute: Annotated[ 
        dict[str, str],
        State.out_field("This field represents a dictionary of commands intended to be "
        "executed on a Linux terminal. Each key-value pair in the dictionary corresponds to an absolute path (the key) and a specific command (the value) to be executed at that path.")
    ]

    # @in
    functions_skeleton:Annotated[
        FunctionSkeleton,
        State.in_field(
            "The well detailed function skeleton for the functions that are in the code."
        )
    ]

    # @in
    test_code: Annotated[
        str, 
        State.in_field(
            "The complete, well-documented working unit test code that adheres to all standards "
            "requested with the programming language, framework user requested "
        )
    ]
    
def add_message(state: SupervisorState, message: tuple[ChatRoles, str]) -> SupervisorState:
    """
    Adds a single message to the messages field in the state.

    Args:
        state (ArchitectState): The current state of the Architect agent.
        message (tuple[str, str]): The message to be added.

    Returns:
        ArchitectState: The updated state with the new message added to the 
        messages field.
    """

    state['messages'] += [message]
    return state
