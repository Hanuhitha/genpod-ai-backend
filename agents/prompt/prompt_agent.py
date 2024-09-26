"""
"""
import os
from typing import Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import ChatOpenAI
from models.constants import ChatRoles, PStatus, Status


from agents.agent.agent import Agent
from agents.prompt.prompt_state import PromptState
from configs.project_config import ProjectAgents
from prompts.prompt_prompts import PromptPrompts
from langchain_core.output_parsers import JsonOutputParser
from utils.logs.logging_utils import logger


class PromptAgent(Agent[PromptState, PromptPrompts]):
    """
    """
    prompt_node_name: str  # The entry point of the graph
    refined_prompt_node_name: str  # END for refining the prompt

    # This is for project comprehensive overview in markdown format
    refined_input_chain: RunnableSequence
    decision_agent_chain: RunnableSequence

    def __init__(self, llm: ChatOpenAI) -> None:
        """
        """

        super().__init__(
            ProjectAgents.prompt.agent_id,
            ProjectAgents.prompt.agent_name,
            PromptState(),
            PromptPrompts(),
            llm
        )
        self.prompt_node_name = "prompt_node"  # The entry point of the graph
        self.refined_prompt_node_name = "refined_prompt_node"  # END point of the graph

        self.refined_input_chain = (
            self.prompts.prompt_generation_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.decision_agent_chain = (
            self.prompts.decision_agent_prompt
            | self.llm
            | JsonOutputParser()
        )

    def add_message(self, message: tuple[ChatRoles, str]) -> None:
        """
        Adds a single message to the messages field in the state.

        Args:
            message (tuple[str, str]): The message to be added.
        """

        self.state['messages'] += [message]

    def router(self, state: PromptState) -> str:
        """
        The entry point for the PromptAgent. Updates the state and refines the prompt based on the user's feedback.

        Args:
            state (PromptState): The current state of the prompt agent.

        Returns: The name of the next node in the graph.
        """

        logger.info(
            f"----{self.agent_name}: Router in action: Determining the next node----")

        if self.state['status'] == False:
            return self.prompt_node_name

        return self.refined_prompt_node_name

    def chat_node(self, state: PromptState) -> PromptState:
        """
        The entry point for the PromptAgent. Updates the state and refines the prompt based on the user's feedback.

        Args:
            state (PromptState): The current state of the prompt agent.

        Returns:
            PromptState: The updated state with refined prompt or additional user feedback.
        """
        logger.info(f"----{self.agent_name}: Initiating Graph Entry Point----")

        # Update the internal state
        self.state = {**state}

        if self.state['status'] == False and len(self.state['original_user_input']) == 0:
            logger.info(f"Please provide the user input :")
            user_input = input("Please provide the user input: \n")
            self.state['original_user_input'] = user_input

        elif not self.state['status']:
            # Invoke the refined input chain for the first time
            refined_response = self.refined_input_chain.invoke({
                "original_user_input": self.state['original_user_input'],
                "messages": self.state['messages']
            })

            self.add_message((
                ChatRoles.AI,
                f"{self.agent_name}: {refined_response['enhanced_prompt']}"

            ))
            logger.info(
                f"This is your structured project input: {refined_response['enhanced_prompt']}")
            logger.info(
                f"Do you like the refined project input (Yes/No) If No, please provide the additional information:")

            output = input(
                "Do you like the refined project input (Yes/No) If No, please provide the additional information:\n")
            self.add_message(((
                ChatRoles.AI,
                f"{self.agent_name}: Do you like the refined project input (Yes/No) If No, please provide the additional information:"

            ),
                (ChatRoles.USER, f"User Response: {output}"

                 )))

            # Check if the refined response meets the criteria using the decision agent
            decision_response = self.decision_agent_chain.invoke({
                "original_user_input": self.state['original_user_input'],
                "messages": self.state['messages'] + [(ChatRoles.AI,  refined_response['enhanced_prompt'])]
            })

            # Add the decision to the messages
            self.add_message(
                (ChatRoles.AI, f"{self.agent_name}: Decision - {decision_response['decision']}"))

            if decision_response['decision'].strip().upper() == 'YES':
                self.state['status'] = True
            else:
                self.state['status'] = False

        return {**self.state}

    def refined_prompt_node(self, state: PromptState) -> PromptState:
        """
        end point for the PromptAgent. Updates the state and refines the prompt based on the user's feedback.

        Args:
            state (PromptState): The current state of the prompt agent.

        Returns:
            PromptState: The updated state with refined prompt or additional user feedback.
        """
        logger.info(f"----{self.agent_name}: Commencing Graph Entry Point----")

        self.state = {**state}
        return {**self.state}

    # def stream(self, input: Dict[str, Any] | Any) -> Iterator[Dict[str, GenericAgentState]]:
    #     """
    #     """
    #     graph_config = {
    #         "configurable": {
    #             "thread_id": self.thread_id
    #         }
    #     }

    #     if self.recursion_limit != -1:
    #         graph_config['recursion_limit'] = self.recursion_limit

    #     return self.graph.app.stream(input, graph_config)
