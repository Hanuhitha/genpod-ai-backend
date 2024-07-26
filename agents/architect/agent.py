"""Architect Agent

This module contains the ArchitectAgent class which is responsible for 
managing the state of the Architect agent, processing user inputs, and 
generating appropriate responses.
"""

from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

from langchain_core.runnables.base import RunnableSequence

from langchain_core.output_parsers import JsonOutputParser

from prompts.architect import ArchitectPrompts

from models.constants import PStatus
from models.constants import Status
from models.constants import ChatRoles

from models.models import Task

from models.architect import ProjectDetails, TaskOutput
from models.architect import QueryResult

from agents.architect.state import ArchitectState

from tools.code import CodeFileWriter

from typing_extensions import Union
from typing_extensions import Literal

from utils.logs.logging_utils import logger

import os

class ArchitectAgent:
    """
    ArchitectAgent Class

    This class represents the Architect agent. It maintains the state of the
    agent, processes user inputs, and generates appropriate responses. It uses 
    a chain of tools to parse the user input and generate a structured output.
    """
    agent_name: str # The name of the agent

    # names of the graph node
    entry_node_name: str # The entry point of the graph
    requirements_node_name: str # Node for handling requirements generation
    additional_info_node_name: str # Node for handling additional information request
    write_requirements_node_name: str # Node for writing requirements to local file system
    tasks_separation_node_name: str  # Node for converting the tasks from string to list
    project_details_node_name: str # Node for gathering project details
    update_state_node_name: str # Node for updating the state

    # local state of this class which is not exposed
    # to the graph state
    mode: Literal["information_gathering", "document_generation"] # information_gathering: when additional information is needed, document_generation: when a requirements document needs to be generated
    generation_step: int # Represents the step at which the current document generation is

    has_error_occured: bool # Indicates if an error occurred when completing a task
    are_tasks_separated: bool # Indicates if tasks have been converted from a string to a list
    is_additional_info_provided: bool # Indicates if additional information is provided when requested
    is_requirements_document_generated: bool # Indicates if the requirements document has been generated
    is_requirements_document_saved: bool # Indicates if the requirements document has been saved locally
    is_additional_info_requested: bool # Indicates if this agent has requested for additional information
    are_project_details_provided: bool # Indicates if project details have been provided

    last_visited_node: str # The last node that was visited in the graph
    error_message: str # The error message, if an error occurred

    state: ArchitectState # Architect agent graphs state
    prompts: ArchitectPrompts # Architect agents the prompts

    llm: Union[ChatOpenAI, ChatOllama] # This is the language learning model (llm) for the Architect agent. It can be either a ChatOpenAI model or a ChatOllama model

    # chains
    project_overview_chain: RunnableSequence # This is for project comprehensive overview in markdown format
    architecture_chain: RunnableSequence
    folder_structure_chain: RunnableSequence
    microservice_design_chain: RunnableSequence
    tasks_breakdown_chain: RunnableSequence
    standards_chain: RunnableSequence
    implementation_details_chain: RunnableSequence
    license_legal_chain: RunnableSequence

    project_details_chain: RunnableSequence # This is for project_name and project folder structure
    additional_information_chain: RunnableSequence
    task_seperation_chain: RunnableSequence

    def __init__(self, llm: Union[ChatOpenAI, ChatOllama]) -> None:
        """
        This method initializes the ArchitectAgent with a given Language Learning Model (llm) 
        and sets up the architect chain. The architect chain is a sequence of operations 
        that the ArchitectAgent will perform to generate a solution architecture.

        Args:
            llm (Union[ChatOpenAI, ChatOllama]): The Language Learning Model to be used by the ArchitectAgent.
        """

        self.agent_name = "Solution Architect"

        self.entry_node_name = "entry"
        self.requirements_node_name = "requirements"
        self.additional_info_node_name = "additional_info"
        self.write_requirements_node_name = "write_requirements"
        self.tasks_separation_node_name = "tasks_seperation"
        self.project_details_node_name = "project_details"
        self.update_state_node_name = "state_update"

        self.mode = ""
        self.generation_step = 0

        self.has_error_occured = False
        self.are_tasks_seperated = False
        self.is_additional_info_provided = False
        self.is_requirements_document_saved = False
        self.is_additional_info_requested = False
        self.is_requirements_document_generated = False
        self.are_project_details_provided = False

        self.last_visited_node = self.entry_node_name # entry point node
        self.error_message = ""

        self.state = ArchitectState()
        self.prompts = ArchitectPrompts()
        
        self.llm = llm

        self.project_overview_chain = ( 
            self.prompts.project_overview_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.architecture_chain = (
            self.prompts.architecture_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.folder_structure_chain = (
            self.prompts.folder_structure_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.microservice_design_chain = (
            self.prompts.microservice_design_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.tasks_breakdown_chain = (
            self.prompts.tasks_breakdown_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.standards_chain = (
            self.prompts.standards_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.implementation_details_chain = (
            self.prompts.implementation_details_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.license_legal_chain = (
            self.prompts.license_details_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.project_details_chain = (
            self.prompts.project_details_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.additional_information_chain = (
            self.prompts.additional_info_prompt
            | self.llm
            | JsonOutputParser()
        )

        self.task_seperation_chain = (
            self.prompts.tasks_separation_prompt
            | self.llm
            | JsonOutputParser()
        )

    def add_message(self, message: tuple[str, str]) -> None:
        """
        Adds a single message to the messages field in the state.

        Args:
            message (tuple[str, str]): The message to be added.
        """

        self.state['messages'] += [message]

    def generate_requirements_document(self) -> str:
        """
        This method generates a requirements document for the project.

        Returns:
            str: A string representing the requirements document.
        """
        
        logger.info(f"----{self.agent_name}: Generating requirements document----")

        return f"""
# Project Requirements Document

{self.state['requirements_overview']['project_details']}

{self.state['requirements_overview']['architecture']}

{self.state['requirements_overview']['folder_structure']}

{self.state['requirements_overview']['microservice_design']}

{self.state['requirements_overview']['task_description']}

{self.state['requirements_overview']['standards']}

{self.state['requirements_overview']['implementation_details']}

{self.state['requirements_overview']['license_details']}
        """
    
    def create_tasks_list(self, tasks_description: list) -> list[Task]:
        """
        This method creates a list of Task objects from a given list of task descriptions
        
        Args:
            tasks_description (list): A list of strings where each string is a description of a task.

        Returns:
            list[Task]: A list of Task objects. Each Task object has a 'description' attribute set 
            from the input list and a 'status' attribute set as NEW.
        """

        logger.info(f"----{self.agent_name}: Initiating the process of Task List Creation----")

        tasks_list: list[Task] = []

        for description in tasks_description:
            tasks_list.append(Task(
                description=description,
                task_status=Status.NEW
            ))   

        return tasks_list

    def request_for_additional_info(self, response: TaskOutput) -> None:
        """
        This method is used when additional information is needed to complete a task. It updates 
        the status of the current task to AWAITING and sets the question for additional info.

        Args:
            response (TaskOutput): The output of the task that requires additional information.
        """

        logger.info(f"----{self.agent_name}: Initiating request for additional information----")

        self.is_additional_info_requested = True
        self.state['current_task'].question = response['question_for_additional_info']
        self.state['current_task'].task_status = Status.AWAITING
    
    def update_requirements_overview(self, key: str, phase: str, response: TaskOutput) -> None:
        """
        This method is used to update the requirements overview with the content generated by a task. 

        Args:
            key (str): The key in the requirements overview to be updated.
            phase (str): The phase of the task.
            response (TaskOutput): The output of the task.
        """
        logger.info(f"----{self.agent_name}: Modifying key: {key} in requirements overview----")

        
        if not response['is_add_info_needed']:
            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {phase} is now ready and prepared."
            ))
            self.state['requirements_overview'][key] = response['content']

            # update to next phase
            self.generation_step += 1
        else:
            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: Additional information has been requested by {phase}."
            ))
            self.request_for_additional_info(response)

    def handle_requirements_overview(self, response: TaskOutput) -> None:
        """
        This method handles the generation of the requirements overview based on the current 
        generation step. It determines which section of the requirements overview to update 
        based on the generation step and calls the 'update_requirements_overview' method with 
        the appropriate parameters.

        Args:
            response (TaskOutput): The output of the task. This contains the generated content 
            for the current section of the requirements overview.
        """
        
        logger.info(f"----{self.agent_name}: Progressing with requirements overview. Current Step: {self.generation_step}----")

        if self.generation_step == 0: # Project Overview
            self.update_requirements_overview("project_details", "Project Overview", response)
        elif self.generation_step == 1: # Architecture
            self.update_requirements_overview("architecture", "Architecture", response)
        elif self.generation_step == 2: # Folder Structure
            self.update_requirements_overview("folder_structure", "Folder Structure", response)
        elif self.generation_step == 3: # Microservice Design
            self.update_requirements_overview("microservice_design", "Microservice Design", response)
        elif self.generation_step == 4: # Tasks Breakdown
            self.update_requirements_overview("task_description", "Tasks Breakdown", response)
        elif self.generation_step == 5: # Standards
            self.update_requirements_overview("standards", "Standards", response)
        elif self.generation_step == 6: # Implementation Details
            self.update_requirements_overview("implementation_details", "Implementation Details", response)
        elif self.generation_step == 7: # License Details
            self.update_requirements_overview("license_details", "License Details", response)

    def router(self, state: ArchitectState) -> str:
        """
        This method acts as a router, determining the next step in the process based on the 
        current state of the Architect agent. It checks the current state and returns the name 
        of the next agent to be invoked. 

        Args:
            state (ArchitectState): The current state of the architect.

        Returns:
            str: The name of the next agent to be invoked.
        """

        logger.info(f"----{self.agent_name}: Router in action: Determining the next node----")

        if self.has_error_occured:
            return self.last_visited_node
        elif self.is_additional_info_requested:
            return self.update_state_node_name
        elif self.mode == "document_generation":
            if not self.is_requirements_document_generated:
                return self.requirements_node_name
            elif not self.is_requirements_document_saved:
                return self.write_requirements_node_name
            elif not self.are_tasks_seperated:
                return self.tasks_separation_node_name
            elif not self.are_project_details_provided:
                return self.project_details_node_name
        elif self.mode == "information_gathering":
            if not self.is_additional_info_provided:
                return self.additional_info_node_name
        
        return self.update_state_node_name
    
    def update_state(self, state: ArchitectState) -> ArchitectState:
        """
        This method updates the current state of the Architect agent with the provided state. 

        Args:
            state (ArchitectState): The new state to update the current state of the agent with.

        Returns:
            ArchitectState: The updated state of the agent.
        """
        logger.info(f"----{self.agent_name}: Proceeding with state update----")
        
        self.state = {**state}

        return {**self.state}
    
    def entry_node(self, state: ArchitectState) -> ArchitectState:
        """
        This method is the entry point of the Architect agent. It updates the current state 
        with the provided state and sets the mode based on the project status and the status 
        of the current task.

        Args:
            state (ArchitectState): The current state of the architect.

        Returns:
            ArchitectState: The updated state of the architect.
        """

        logger.info(f"----{self.agent_name}: Initiating Graph Entry Point----")

        self.state={**state}
        self.last_visited_node = self.entry_node_name
        self.is_additional_info_requested = False
        
        if self.state['project_status'] == PStatus.INITIAL.value:
            self.mode = "document_generation"
        elif self.state["current_task"].task_status.value == Status.AWAITING.value:
            self.mode = "information_gathering"

        return {**self.state}

    def requirements_node(self, state: ArchitectState) -> ArchitectState:
        """
        This method is responsible for generating the requirements overview. 

        Args:
            state (ArchitectState): The current state of the architect.

        Returns:
            ArchitectState: The updated state of the architect.
        """
        logger.info(f"----{self.agent_name}: Commencing generation of Requirements Document----")

        if (not self.has_error_occured) and (not self.is_additional_info_requested):
            state['requirements_overview'] = {}
            self.generation_step = 0
            
        self.state={**state}
        self.last_visited_node = self.requirements_node_name
        self.is_additional_info_requested = False

        self.add_message((
            ChatRoles.USER.value,
            f"{self.agent_name}: Initiating the process of preparing the requirements overview."
        ))

        try:
            if self.generation_step == 0: #0. Project Overview
                self.add_message((
                    ChatRoles.USER.value,
                    f"{self.agent_name}: Progressing with Step 0 - Project Overview."
                ))

                response: TaskOutput = self.project_overview_chain.invoke({
                    "user_request": f"{self.state['user_request']}",
                    "task_description": f"{self.state['current_task'].description}",
                    "additional_information": f"{self.state['current_task'].additional_info}"
                })

                self.has_error_occured = False
                self.error_message = ""
                self.handle_requirements_overview(response)

            if self.generation_step == 1: # 1. Architecture
                self.add_message((
                    ChatRoles.USER.value,
                    f"{self.agent_name}: Progressing with Step 1 - Architecture."
                ))

                response: TaskOutput = self.architecture_chain.invoke({
                    "project_overview": f"{self.state['requirements_overview']['project_details']}",
                })

                self.has_error_occured = False
                self.error_message = ""
                self.handle_requirements_overview(response)

            if self.generation_step == 2: # 2. Folder Structure
                self.add_message((
                    ChatRoles.USER.value,
                    f"{self.agent_name}: Progressing with Step 2 - Folder Structure."
                ))

                response: TaskOutput = self.folder_structure_chain.invoke({
                    "project_overview": f"{self.state['requirements_overview']['project_details']}",
                    "architecture": f"{self.state['requirements_overview']['architecture']}",
                })

                self.has_error_occured = False
                self.error_message = ""
                self.handle_requirements_overview(response)

            if self.generation_step == 3: # 3. Micro service Design
                self.add_message((
                    ChatRoles.USER.value,
                    f"{self.agent_name}: Progressing with Step 3 - Microservice Design."
                ))

                response: TaskOutput = self.microservice_design_chain.invoke({
                    "project_overview": f"{self.state['requirements_overview']['project_details']}",
                    "architecture": f"{self.state['requirements_overview']['architecture']}",
                })

                self.has_error_occured = False
                self.error_message = ""
                self.handle_requirements_overview(response)

            if self.generation_step == 4: # 4. Tasks Breakdown
                self.add_message((
                    ChatRoles.USER.value,
                    f"{self.agent_name}: Progressing with Step 4 - Tasks Breakdown."
                ))

                response: TaskOutput = self.tasks_breakdown_chain.invoke({
                    "project_overview": f"{self.state['requirements_overview']['project_details']}",
                    "architecture": f"{self.state['requirements_overview']['architecture']}",
                    "microservice_design": f"{self.state['requirements_overview']['microservice_design']}",
                })

                self.has_error_occured = False
                self.error_message = ""
                self.handle_requirements_overview(response)

            if self.generation_step == 5: # 5. Standards
                self.add_message((
                    ChatRoles.USER.value,
                    f"{self.agent_name}: Progressing with Step 5 - Standards."
                ))

                response: TaskOutput = self.standards_chain.invoke({
                    "user_request": f"{self.state['user_request']}\n",
                    "task_description": f"{self.state['requirements_overview']['task_description']}",
                })

                self.has_error_occured = False
                self.error_message = ""
                self.handle_requirements_overview(response)

            if self.generation_step == 6: # 6. Implementation Details
                self.add_message((
                    ChatRoles.USER.value,
                    f"{self.agent_name}: Progressing with Step 6 - Implementation Details."
                ))

                response: TaskOutput = self.implementation_details_chain.invoke({
                "architecture": f"{self.state['requirements_overview']['architecture']}\n",
                "microservice_design": f"{self.state['requirements_overview']['microservice_design']}",
                "folder_structure": f"{self.state['requirements_overview']['folder_structure']}",
                })

                self.has_error_occured = False
                self.error_message = ""
                self.handle_requirements_overview(response)

            if self.generation_step == 7: # 7. License Details
                self.add_message((
                    ChatRoles.USER.value,
                    f"{self.agent_name}: Progressing with Step 7 - License Details."
                ))

                response: TaskOutput = self.license_legal_chain.invoke({
                    "user_request": f"{self.state['user_request']}",
                    "license_text": f"{self.state['license_text']}",
                })

                self.has_error_occured = False
                self.error_message = ""
                self.handle_requirements_overview(response)

            if self.generation_step == 8:
                self.is_requirements_document_generated = True
        except Exception as e:
            self.has_error_occured = True
            self.error_message = f"An error occurred while processing the request: {str(e)}"

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {self.error_message}"
            ))
            logger.error(f"Exception: {type(e)} --> {self.agent_name}: {self.error_message}")

        return {**self.state}


    def write_requirements_node(self, state: ArchitectState) -> ArchitectState:
        """
        This method is used to write the requirements overview to a local file. It updates 
        the state of the architect and sets the `is_requirements_document_saved` flag to True if 
        the requirements are successfully written.

        Args:
            state (ArchitectState): The current state of the architect.

        Returns:
            ArchitectState: The updated state of the architect.
        """

        logger.info(f"----{self.agent_name}: Commencing the process of writing requirements documents to local filesystem----")

        self.state={**state}

        document = self.generate_requirements_document()
        if len(document) < 0:
            self.has_error_occured = True
            self.error_message = "ERROR: Found requirements document to be empty. Could not write it to file system."
            self.last_visited_node = self.requirements_node_name
            
            self.add_message((
                ChatRoles.USER.value,
                self.error_message,
            ))
        else:
            generated_code = document
            file_path = os.path.join(self.state['generated_project_path'], "docs/requirements.md")

            self.has_error_occured, msg = CodeFileWriter.write_generated_code_to_file.invoke({"generated_code": generated_code, "file_path": file_path})
            
            # if self.has_error_occured:
            #     self.error_message = msg
            #     self.last_visited_node = self.requirements_and_additional_context
            # else:
            self.has_error_occured = False
            self.error_message = ""
            self.last_visited_node = self.write_requirements_node_name
            self.is_requirements_document_saved = True

            self.add_message((
                ChatRoles.USER.value,
                msg
            ))

        return {**self.state}

    def tasks_separation_node(self, state: ArchitectState) -> ArchitectState:
        """
        This method separates tasks from the requirements document and creates a list of tasks.
        It updates the state of the architect with the separated tasks.

        Args:
            state (ArchitectState): The current state of the architect.

        Returns:
            ArchitectState: The updated state of the architect.
        """

        logger.info(f"----{self.agent_name}: Initiating the process of Tasks Separation----")

        self.last_visited_node = self.tasks_separation_node_name
        self.state={**state}

        try:
            task_seperation_solution = self.task_seperation_chain.invoke({
                "tasks": self.state['requirements_overview']['task_description'],
                "error_message": self.error_message
            })
            
            self.has_error_occured = False
            self.error_message = ""
            
            tasks = task_seperation_solution['tasks']

            if not isinstance(tasks, list):
                raise TypeError(f"Expected 'tasks' to be of type list but received {type(tasks).__name__}.")

            if not tasks:
                raise ValueError(f"The 'tasks' list received from the previous response is empty. Received: {tasks}, Expected: Non empty list of strings.")
   
            self.state['tasks'] = self.create_tasks_list(tasks)

            self.are_tasks_seperated = True
            self.add_message((
                ChatRoles.USER.value,
               f"{self.agent_name}: Task list has been successfully created. You can now proceed with your tasks."
            ))

        except ValueError as ve:
            self.has_error_occured = True
            self.error_message = f"ValueError occurred: {ve}"

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {self.error_message}"
            ))
            logger.error(f"Exception: {type(ve)} --> {self.agent_name}: {self.error_message}")
        except TypeError as te:
            self.has_error_occured = True
            self.error_message = f"TypeError occurred: {te}"

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {self.error_message}"
            ))
            logger.error(f"Exception: {type(te)} --> {self.agent_name}: {self.error_message}")
        except Exception as e:
            self.has_error_occured = True
            self.error_message = f"An unexpected error occurred: {e}"

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {self.error_message}" 
            ))           
            logger.error(f"Exception: {type(e)} --> {self.agent_name}: {self.error_message}")

        return {**self.state}

    def project_details_node(self, state: ArchitectState) -> ArchitectState:
        """
        This method is used to gather project details. It updates the current state with the 
        provided state and invokes the project_details_chain to get the project details.

        Args:
            state (ArchitectState): The current state of the architect.

        Returns:
            ArchitectState: The updated state of the architect.
        """

        logger.info(f"----{self.agent_name}: Initiating the process of gathering project details----")

        self.state={**state}
        self.last_visited_node = self.project_details_node_name

        self.add_message((
            ChatRoles.USER.value,
            f"{self.agent_name}: Initiating the process of gathering project details."
        ))

        try:
            response: ProjectDetails = self.project_details_chain.invoke({
                "user_request": f"{self.state['user_request']}\n",
                "folder_structure_document": f"{self.state['requirements_overview']['folder_structure']}\n",
                "error_message": f"{self.error_message}\n",
            })

            self.has_error_occured = False
            self.error_message = ""

            required_keys = ["project_name", "project_folder_structure"]
            missing_keys = [key for key in required_keys if key not in response]

            if missing_keys:
                raise KeyError(f"Missing keys: {missing_keys} in the response. Try Again!")

            self.state['project_name'] = response['project_name']
            self.state['project_folder_structure'] = response['project_folder_structure']
          
            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: Project details have been successfully gathered!"
            ))

            self.are_project_details_provided = True
            self.state['current_task'].task_status = Status.DONE
        except Exception as e:
            self.has_error_occured = True
            self.error_message = f"An error occurred while processing the request: {str(e)}"

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {self.error_message}"
            ))

            logger.error(f"Exception: {type(e)} --> {self.agent_name}: {self.error_message}")

        return {**self.state}
    
    def additional_information_node(self, state: ArchitectState) -> ArchitectState:
        """
        This method is used to gather additional information if needed. It updates the current 
        state with the provided state and invokes the additional_information_chain to get the 
        additional information.

        Args:
            state (ArchitectState): The current state of the architect.

        Returns:
            ArchitectState: The updated state of the architect.
        """
        
        logger.info(f"----{self.agent_name}: Working on gathering additional information----")

        self.state={**state}
        self.last_visited_node = self.additional_info_node_name

        self.add_message((
            ChatRoles.USER.value,
            f"{self.agent_name}: Started working on gathering the additional information."
        ))
        
        try:
            llm_response: QueryResult = self.additional_information_chain.invoke({
                "requirements_document": self.generate_requirements_document(),
                "question": self.state['current_task'].question,
                "error_message": self.error_message
            })

            self.has_error_occured = False
            self.error_message = ""

            required_keys = ["is_answer_found", "response_text"]
            missing_keys = [key for key in required_keys if key not in llm_response]

            if missing_keys:
                raise KeyError(f"Missing keys: {missing_keys} in the response. Try Again!")

            self.state["query_answered"] = llm_response['is_answer_found']
            
            response_text = llm_response['response_text'] if self.state["query_answered"] else "I don't have any additional information about the question."
            self.state["current_task"].additional_info = f"{self.state['current_task'].additional_info}, \nArchitect_Response:\n{response_text}"

            message_text = "Additional information has been successfully provided." if self.state["query_answered"] else "Unfortunately, I couldn't provide the additional information requested."

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {message_text}"
            ))

            self.is_additional_info_provided = True
        except Exception as e:
            self.has_error_occured = True
            self.error_message = f"An error occurred while processing the request: {str(e)}"

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {self.error_message}"
            ))

            logger.error(f"Exception: {type(e)} --> {self.agent_name}: {self.error_message}")
            
        return {**self.state}
