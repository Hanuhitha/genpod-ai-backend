"""
"""
import os
from typing import Literal
import time
from fastapi import WebSocket
import requests
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import ChatOpenAI
import requests
from pydantic_models.constants import ChatRoles, PStatus, Status
from rich.console import Console
from agents.agent.agent import Agent
from agents.prompt_agent.prompt_state import PromptState
from configs.project_config import ProjectAgents
from prompts.prompt_prompts import PromptPrompts
from langchain_core.output_parsers import JsonOutputParser
from utils.logs.logging_utils import logger
import websockets
from websockets.exceptions import ConnectionClosedError
import asyncio

console = Console()


class PromptAgent(Agent[PromptState, PromptPrompts]):
    """
    """
    prompt_node_name: str  # The entry point of the graph
    refined_prompt_node_name: str  # END for refining the prompt

    # This is for project comprehensive overview in markdown format
    refined_input_chain: RunnableSequence
    decision_agent_chain: RunnableSequence

    def __init__(self, llm: ChatOpenAI, websocket: WebSocket) -> None:
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

        self.websocket = websocket

        self.max_retries = 30
        self.retry_interval = 2

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

    async def chat_node(self, state: PromptState) -> PromptState:
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
            user_input = state['original_user_input']
            self.state['original_user_input'] = user_input

        elif not self.state['status']:
            # Invoke the refined input chain for the first time
            refined_response = await self.refined_input_chain.ainvoke({
                "original_user_input": self.state['original_user_input'],
                "messages": self.state['messages']
            })

            self.add_message((
                ChatRoles.AI,
                f"{self.agent_name}: {refined_response['enhanced_prompt']}"

            ))
            logger.info(
                f"This is your structured project input: {refined_response['enhanced_prompt']}")

            await self.websocket.send(f"Refined Response: {refined_response['enhanced_prompt']}")

            await self.post_enhanced_prompt(refined_response['enhanced_prompt'], self.websocket, self.state['request_id'])

            logger.info(
                f"Do you like the refined project input (Yes/No) If No, please provide the additional information:")

            # Get additional info from WebSocket (user feedback)
            user_response = await self.get_additional_info_via_websocket(
                self.websocket, self.state['request_id'])
            self.add_message(((
                ChatRoles.AI,
                f"{self.agent_name}: Do you like the refined project input (Yes/No) If No, please provide the additional information:"

            ),
                (ChatRoles.USER, f"User Response: {user_response}"

                 )))

            # Check if the refined response meets the criteria using the decision agent
            decision_response = await self.decision_agent_chain.ainvoke({
                "original_user_input": self.state['original_user_input'],
                "messages": self.state['messages'] + [(ChatRoles.AI,  refined_response['enhanced_prompt'])]
            })

            # Add the decision to the messages
            self.add_message(
                (ChatRoles.AI, f"{self.agent_name}: Decision - {decision_response['decision']}"))

            await self.websocket.send(f"Decision result: {decision_response['decision']}")

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

    async def get_additional_info_via_websocket(self, websocket: WebSocket, request_id: int) -> str:
        """
        Listen for additional information from the WebSocket.
        """
        try:
            while True:
                message = await websocket.recv()
                message_data = eval(message)
                if "additional_input" in message_data and message_data['request_id'] == request_id:
                    additional_input = message_data['additional_input']
                    console.print(
                        f"[green]Received additional input: {additional_input}[/green]")
                    if len(additional_input) == 0:
                        continue
                    else:
                        return additional_input

        except websockets.exceptions.ConnectionClosedError:
            logger.error(
                f"WebSocket connection closed unexpectedly while waiting for additional input.")

        except Exception as e:
            logger.error(f"Error receiving additional input: {e}")

        return ""

    async def post_enhanced_prompt(self, prompt, websocket, request_id):
        """
        Post the enhanced prompt to both the WebSocket (for CLI) and the database.
        """
        llm_response = {
            "llm_output_prompt_message_response": prompt,
            "response_id": self.state['request_id']
        }

        try:
            # # Send the prompt to the WebSocket for the CLI
            # if websocket:
            #     try:
            #         await websocket.send(f"Refined Response: {prompt}")
            #         logger.info(
            #             f"Sent enhanced prompt to CLI via WebSocket for request_id {request_id}")
            #     except ConnectionClosedError as e:
            #         logger.error(f"WebSocket connection closed: {e}")
            #         return

            #  Post the enhanced prompt to the database via FastAPI
            url = f'http://localhost:8000/update_conversation/{request_id}'
            response = requests.put(url, json=llm_response)
            response.raise_for_status()

            returned_data = response.json()
            logger.info(f"Enhanced prompt posted to database! {returned_data}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting enhanced prompt to the database: {e}")

    # def post_enhanced_prompt(self, prompt):
    #     llm_response = {
    #         "llm_output_prompt_message_response": prompt,
    #         "response_id": self.state['request_id']
    #     }

    #     try:
    #         request_id = self.state['request_id']
    #         url = f'http://localhost:8000/update_conversation/{request_id}'
    #         response = requests.put(url, json=llm_response)
    #         response.raise_for_status()

    #         returned_data = response.json()
    #         logger.info("posted! %s", returned_data)

    #     except requests.exceptions.RequestException as e:
    #         logger.error("Error creating project input: %s", e)

    def additional_info(self, prompt):
        self.state['request_id'] = self.state['request_id'] + 1
        additional_info = {
            "user_input_prompt_message": prompt,
            "request_id": self.state['request_id']
        }
        try:
            response = requests.post(
                "http://localhost:8000/additional_input", json=additional_info)
            response.raise_for_status()

            returned_data = response.json()
            logger.info("Project Input has been created! %s",
                        returned_data['user_input_prompt_message'])
            return returned_data['user_input_prompt_message']

        except requests.exceptions.RequestException as e:
            logger.error("Error creating project input: %s", e)

    # def get_user_input(self):
    #     try:
    #         response = requests.get("http://localhost:8000/additional_info")
    #         response.raise_for_status()

    #         project_data = response.json()
    #         logger.info("Retrieved %d additional user inputs.",
    #                     len(project_data))
    #         return project_data
    #     except requests.exceptions.RequestException as e:
    #         logger.error("Error retrieving project inputs: %s", e)
    #         return None

    # def get_enhanced_prompt(self, request_id: int):
    #     retries = 5

    #     while retries < self.max_retries:
    #         try:
    #             response = requests.get(
    #                 f"http://localhost:8000/enhanced_prompt/{request_id}")
    #             response.raise_for_status()
    #             data = response.json()
    #             if data.get("llm_output_prompt_message_response"):
    #                 logger.info("Enhanced prompt found.")
    #                 return data
    #             else:
    #                 logger.info(
    #                     "Enhanced prompt not available yet. Retrying in %d seconds...",
    #                     self.retry_interval
    #                 )

    #         except requests.exceptions.RequestException as e:
    #             logger.error("Error retrieving enhanced prompt: %s", e)
    #             return None

    #         time.sleep(self.retry_interval)
    #         retries += 1

    #     logger.error(
    #         "Max retries reached. Enhanced prompt not found for request ID: %s", request_id)
    #     return None
