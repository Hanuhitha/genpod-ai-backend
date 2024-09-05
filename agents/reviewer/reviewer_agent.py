"""
"""
import os
from typing import Literal

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import ChatOpenAI

from agents.agent.agent import Agent
from agents.reviewer.reviewer_state import ReviewerState
from configs.project_config import ProjectAgents
from prompts.reviewer_prompts import ReviewerPrompts


class ReviewerAgent(Agent[ReviewerState]):
    """
    """

    def __init__(self, llm: ChatOpenAI) -> None:
        """
        """

        super().__init__(
            ProjectAgents.reviewer.agent_id,
            ProjectAgents.reviewer.agent_name,
            ReviewerState(),
            ReviewerPrompts(),
            llm
        )