"""
"""

from typing_extensions import Annotated, TypedDict
from agents.agent.state import State
from pydantic_models.constants import ChatRoles


class PromptState(TypedDict):
    """
    """
    original_user_input: Annotated[
        str,
        State.in_field(
            "The original set of requirements provided by the user, serving as the "
            "foundation for the project."
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
    status: Annotated[
        bool,
        State.in_field(
            "Status of the input refinement process."
        )
    ]
    request_id: Annotated[
        int,
        State.in_field(
            "user request id"
        )
    ]
