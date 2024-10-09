""" Graph State for Planner Agent """
from typing import Dict, List

from typing_extensions import Annotated, TypedDict

from agents.agent.state import State
from models.models import PlannedTaskQueue, Task


class PlannerState(TypedDict):
    """
    Represents the state of our Planner Retriever.

    Attributes:
        deliverable: Individual deliverables identified by the Architect
        details: LLM generation of the minute details needed to complete each task
        response: list of Task packets to main all older responses.
    """

    # @in
    project_path: Annotated[
        str,
        State.in_field()
    ]

    # @in
    context: Annotated[
        str,
        State.in_field("Requirements document  and rag retrivial info.")
    ]

    # @inout
    current_task: Annotated[
        Task,
        State.inout_field()
    ]

    # @out
    planned_tasks: Annotated[
        PlannedTaskQueue,
        State.out_field("A list of work packages planned by the planner")
    ]

    # @out - not needed
    response: Annotated[
        List[Task],
        State.out_field()
    ]
