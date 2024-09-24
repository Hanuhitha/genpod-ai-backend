# """
# """
# import os
# from typing import Literal

# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.runnables.base import RunnableSequence
# from langchain_openai import ChatOpenAI

# from agents.agent.agent import Agent
# from agents.prompt.prompt_state import PromptState
# from configs.project_config import ProjectAgents
# from prompts.prompt_prompts import PromptPrompts


# class PromptAgent(Agent[PromptState,PromptPrompts]):
#     """
#     """

#     def __init__(self, llm: ChatOpenAI) -> None:
#         """
#         """

#         super().__init__(
#             ProjectAgents.prompt.agent_id,
#             ProjectAgents.prompt.agent_name,
#             PromptState(),
#             PromptPrompts(),
#             llm
#         )
