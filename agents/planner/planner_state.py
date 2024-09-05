""" Graph State for Planner Agent """
from typing import Dict, List

from typing_extensions import Annotated, TypedDict

from agents.agent.state import State
from models.models import Task


class PlannerState(TypedDict):
    """
    Represents the state of our Planner Retriever.

    Attributes:
        deliverable: Individual deliverables identified by the Architect
        details: LLM generation of the minute details needed to complete each task
        response: list of Task packets to main all older responses.
    """

    # @in
    deliverable: Annotated[
        List[str],
        State.in_field()
    ]

    # @in
    project_path: Annotated[
        str,
        State.in_field()
    ]

    # @inout
    current_task: Annotated[
        Task,
        State.inout_field()
    ]

    # @out
    response: Annotated[
        List[Task],
        State.out_field()
    ]

    # @out
    backlogs: Annotated[
        List[str],
        State.out_field()
    ]

    # @out
    planned_task_map: Annotated[
        Dict[str, Dict[str, bool]],
        State.out_field()
    ]

    # @out
    planned_task_requirements: Annotated[
        Dict[str,str],
        State.out_field()
    ]
