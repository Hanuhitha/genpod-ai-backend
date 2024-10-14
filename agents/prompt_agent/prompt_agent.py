"""
"""
import os
from typing import Literal
import time
from pydantic import ValidationError
import requests
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import ChatOpenAI
import requests
from policies.pydantic_models.prompt_models import Prompt_Generation, Decision_Agent
from prompt_loader.prompt_loader import load_prompts_from_yaml
from agents.agent.agent import Agent
from agents.prompt_agent.prompt_state import PromptState
from configs.project_config import ProjectAgents
from langchain_core.output_parsers import JsonOutputParser
from policies.pydantic_models.constants import ChatRoles
from utils.logs.logging_utils import logger
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser


class PromptAgent(Agent[PromptState, None]):
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
            None,
            llm
        )
        self.prompt_node_name = "prompt_node"  # The entry point of the graph
        self.refined_prompt_node_name = "refined_prompt_node"  # END point of the graph

        yaml_file_path = "/opt/genpod/system_prompts_default_yaml/prompt_enhancer_prompt.yml"

        # configurable_file_path = "/opt/genpod/system_prompts_configurable_yaml/prompt_enhancer_prompt.yml"

        self.max_retries = 500
        self.retry_interval = 3
        # try:
        #     self.prompts = load_prompts_from_yaml(configurable_file_path)
        #     logger.info("Prompts loaded successfully from YAML.")
        # except (FileNotFoundError, ValidationError) as e:
        #     logger.error(f"Failed to load prompts: {e}")
        #     raise

        try:
            self.prompts = load_prompts_from_yaml(yaml_file_path)
            logger.info("Prompts loaded successfully from YAML.")
        except (FileNotFoundError, ValidationError) as e:
            logger.error(f"Failed to load prompts: {e}")
            raise

    #  # Paths to YAML configuration files
    #     system_yaml_file_path = "/opt/genpod/system_prompts_yaml/prompt_enhancer_prompt.yml"
    #     user_yaml_file_path = "/opt/genpod/system_prompts_configurable_yaml/prompt_enhancer_prompt.yml"

    #     self.max_retries = 500
    #     self.retry_interval = 3

    #     # Load system prompts
    #     try:
    #         self.system_config = load_prompts_from_yaml(system_yaml_file_path)
    #         logger.info("System prompts loaded successfully from YAML.")
    #     except (FileNotFoundError, ValidationError) as e:
    #         logger.error(f"Failed to load system prompts: {e}")
    #         raise

    #     # Load user prompts
    #     try:
    #         self.user_config = load_prompts_from_yaml(user_yaml_file_path)
    #         logger.info("User prompts loaded successfully from YAML.")
    #     except (FileNotFoundError, ValidationError) as e:
    #         logger.error(f"Failed to load user prompts: {e}")
    #         raise

    #     user_input_variables = self.configurable_prompts.prompt_generation_prompt.user_input_variables

        prompt_template = self.prompts.prompt_generation_prompt.template
        input_variables = self.prompts.prompt_generation_prompt.input_variables
        partial_variables = self.prompts.prompt_generation_prompt.partial_variables
        partial_variables['format_instructions'] = PydanticOutputParser(
            pydantic_object=Prompt_Generation).get_format_instructions()
        self.prompts.prompt_generation_prompt = PromptTemplate(
            template=prompt_template,
            input_variables=input_variables,
            partial_variables=partial_variables
        )

        decision_template = self.prompts.decision_agent_prompt.template
        input_variables = self.prompts.decision_agent_prompt.input_variables
        partial_variables = self.prompts.decision_agent_prompt.partial_variables
        partial_variables['format_instructions'] = PydanticOutputParser(
            pydantic_object=Decision_Agent).get_format_instructions()
        self.prompts.decision_agent_prompt = PromptTemplate(
            template=decision_template,
            input_variables=input_variables,
            partial_variables=partial_variables
        )
        # self.refined_input_chain = self.prompts.prompt_generation_prompt

        self.refined_input_chain = (
            self.prompts.prompt_generation_prompt
            | self.llm
            | JsonOutputParser()
        )

        # Create decision agent chain using the `|` operator for compatibility with LangChain
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
            user_input = state['original_user_input']
            self.state['original_user_input'] = user_input

        elif not self.state['status']:
            # Invoke the refined input chain for the first time
            refined_response = self.refined_input_chain.invoke({
                "original_user_input": self.state['original_user_input'],
                "messages": self.state['messages'],
            })

            self.add_message((
                ChatRoles.AI,
                f"{self.agent_name}: {refined_response['enhanced_prompt']}"

            ))
            logger.info(
                f"This is your structured project input: {refined_response['enhanced_prompt']}")

            self.post_enhanced_prompt(
                refined_response['enhanced_prompt'])

            logger.info(
                f"Do you like the refined project input (Yes/No) If No, please provide the additional information:")

            user_response = self.additional_info(
                prompt="I need to refine the project input. Add more test cases.")

            self.add_message(((
                ChatRoles.AI,
                f"{self.agent_name}: Do you like the refined project input (Yes/No) If No, please provide the additional information:"

            ),
                (ChatRoles.USER, f"User Response: {user_response}"

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

    def post_enhanced_prompt(self, prompt):
        llm_response = {
            "llm_output_prompt_message_response": prompt,
            "response_id": self.state['request_id']
        }

        try:
            request_id = self.state['request_id']
            url = f'http://localhost:8000/update_conversation/{request_id}'
            response = requests.put(url, json=llm_response)
            response.raise_for_status()

            returned_data = response.json()
            logger.info("posted! %s", returned_data)

        except requests.exceptions.RequestException as e:
            logger.error("Error creating project input: %s", e)

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

    def get_user_input(self):
        try:
            response = requests.get("http://localhost:8000/additional_info")
            response.raise_for_status()

            project_data = response.json()
            logger.info("Retrieved %d additional user inputs.",
                        len(project_data))
            return project_data
        except requests.exceptions.RequestException as e:
            logger.error("Error retrieving project inputs: %s", e)
            return None

    def get_enhanced_prompt(self, request_id: int):
        retries = 0

        while retries < self.max_retries:
            try:
                response = requests.get(
                    f"http://localhost:8000/enhanced_prompt/{request_id}")
                response.raise_for_status()
                data = response.json()
                if data.get("llm_output_prompt_message_response"):
                    logger.info("Enhanced prompt found.")
                    return data
                else:
                    logger.info(
                        "Enhanced prompt not available yet. Retrying in %d seconds...",
                        self.retry_interval
                    )

            except requests.exceptions.RequestException as e:
                logger.error("Error retrieving enhanced prompt: %s", e)
                return None

            time.sleep(self.retry_interval)
            retries += 1

        logger.error(
            "Max retries reached. Enhanced prompt not found for request ID: %s", request_id)
        return None
