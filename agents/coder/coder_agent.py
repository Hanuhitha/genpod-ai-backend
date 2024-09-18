"""Coder Agent
"""
import os
from typing import Literal, List

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import ChatOpenAI

from agents.agent.agent import Agent
from agents.coder.coder_state import CoderState
from configs.project_config import ProjectAgents
from models.coder_models import CodeGenerationPlan
from models.constants import ChatRoles, Status
from prompts.coder_prompts import CoderPrompts
from tools.code import CodeFileWriter
from tools.license import License
from tools.shell import Shell
from utils.logs.logging_utils import logger


class CoderAgent(Agent[CoderState, CoderPrompts]):
    """
    """

    # names of the graph node
    entry_node_name: str # The entry point of the graph
    code_generation_node_name: str 
    general_task_node_name: str
    run_commands_node_name: str
    write_generated_code_node_name: str
    download_license_node_name: str 
    add_license_node_name: str
    agent_response_node_name: str
    update_state_node_name: str 

    mode: Literal["code_generation", "general_task"]

    # local state of this class which is not exposed
    # to the graph state
    is_code_generated: bool
    has_command_execution_finished: bool
    has_code_been_written_locally: bool
    is_license_file_downloaded: bool # This is one time updated flag
    is_license_text_added_to_files: bool
    hasPendingToolCalls: bool

    last_visited_node: str
    error_message: str

    current_code_generation_plan_list: List[CodeGenerationPlan]

    # chains
    code_generation_chain: RunnableSequence

    def __init__(self, llm: ChatOpenAI) -> None:
        """
        """
        
        super().__init__(
            ProjectAgents.coder.agent_id,
            ProjectAgents.coder.agent_name,
            CoderState(),
            CoderPrompts(),
            llm
        )

        self.entry_node_name = "entry"
        self.code_generation_node_name = "code_generation"
        self.general_task_node_name = "general_task"
        self.run_commands_node_name = "run_commands"
        self.write_generated_code_node_name = "write_code"
        self.download_license_node_name = "download_license"
        self.add_license_node_name = "add_license_text"
        self.agent_response_node_name = "agent_response"
        self.update_state_node_name = "state_update"

        self.mode = ""

        self.is_code_generated = False
        self.has_command_execution_finished = False
        self.has_code_been_written_locally = False
        self.is_license_file_downloaded = False
        self.is_license_text_added_to_files = False
        self.hasPendingToolCalls = False

        self.last_visited_node = self.entry_node_name
        self.error_message = ""

        self.current_code_generation_plan_list = []

        self.code_generation_chain = (
            self.prompts.code_generation_prompt
            | self.llm
            | JsonOutputParser()
        )

    def add_message(self, message: tuple[ChatRoles, str]) -> None:
        """
        Adds a single message to the messages field in the state.

        Args:
            message (tuple[str, str]): The message to be added.
        """
        if self.state['messages'] is None:
            self.state['messages'] = [message]
        else:
            self.state['messages'] += [message]

    def router(self, state: CoderState) -> str:
        """
        """

        if self.mode == "code_generation":
            if not self.is_code_generated:
                return self.code_generation_node_name
        elif self.mode == "general_task":
            if not self.is_code_generated:
                return self.general_task_node_name

        if not self.is_license_file_downloaded:
            return self.download_license_node_name
        else:
            return self.agent_response_node_name

    def entry_node(self, state: CoderState) -> CoderState:
        """
        This method is the entry point of the Coder agent. It updates the current state 
        with the provided state and sets the mode based on the project status and the status 
        of the current task.

        Args:
            state (CoderState): The current state of the coder.

        Returns:
            CoderState: The updated state of the coder.
        """

        logger.info(f"----{self.agent_name}: Initiating Graph Entry Point----")
        self.state = state

        self.last_visited_node = self.entry_node_name

        if self.state['current_planned_task'].task_status == Status.NEW:
            if self.state['current_planned_task'].is_function_generation_required:
                self.mode = "code_generation"
            else:
                self.mode = "general_task"
            
            self.is_code_generated = False
            self.has_command_execution_finished = False
            self.has_code_been_written_locally = False
            self.is_license_text_added_to_files = False
            self.hasPendingToolCalls = False

            self.current_code_generation_plan_list = []

        return self.state
    
    def general_task_node(self, state: CoderState) -> CoderState:
        """
        """
        logger.info(f"----{self.agent_name}: Initiating general task Generation for Task Id: {state['current_planned_task'].task_id}----")

        self.state = state
        self.last_visited_node = self.code_generation_node_name

        task = self.state["current_planned_task"]
        logger.info(f"----{self.agent_name}: Started working on the task: {task.description}.----")
        
        self.add_message((
            ChatRoles.USER,
            f"Started working on the task: {task.description}."
        ))

        # TODO: Multiple files can be generated during this phase. Need to change logic to only 
        # generate single file at a time.
        while True:
            try:
                llm_response: CodeGenerationPlan = self.code_generation_chain.invoke({
                    "project_name": self.state['project_name'],
                    "project_path": os.path.join(self.state['project_path'], self.state['project_name']),
                    "requirements_document": self.state['requirements_document'],
                    "error_message": self.error_message,
                    "task": task.description,
                    "functions_skeleton": "no function sekeletons available for this task.",
                    "unit_test_cases": "no unit test cases available for this task."
                })

                cleaned_response = CodeGenerationPlan(**llm_response)
                self.current_code_generation_plan_list.append(cleaned_response)

                self.error_message = ""
                
                break # while loop exit
            except Exception as e:
                logger.error(f"{self.agent_name}: Error Occured at general task generation: ===>{type(e)}<=== {e}.----")
   
                self.error_message = e
                self.add_message((
                    ChatRoles.USER,
                    f"{self.agent_name}: {self.error_message}"
                ))
        
        self.add_message((
            ChatRoles.USER,
            f"{self.agent_name}: Code Generation completed!"
        ))
        self.is_code_generated = True
        
        return self.state

    def code_generation_node(self, state: CoderState) -> CoderState:
        """
        """
        logger.info(f"----{self.agent_name}: Initiating Code Generation for Task Id: {state['current_planned_task'].task_id}----")

        self.state = state
        self.last_visited_node = self.code_generation_node_name

        task = self.state["current_planned_task"]
        logger.info(f"----{self.agent_name}: Started working on the task: {task.description}.----")
  
        self.add_message((
            ChatRoles.USER,
            f"Started working on the task: {task.description}."
        ))
        
        # TODO: Need to re define the data structure being used for `functions_skeleton`
        for file_path, function_skeleton in self.state['functions_skeleton'].items():
            logger.info(f"{self.agent_name}: working on code generation for file_path: {file_path}.")

            while True:

                try:
                    llm_response = self.code_generation_chain.invoke({
                        "project_name": self.state['project_name'],
                        "project_path": os.path.join(self.state['project_path'], self.state['project_name']),
                        "requirements_document": self.state['requirements_document'],
                        "error_message": self.error_message,
                        "task": task.description,
                        "functions_skeleton": {file_path: function_skeleton},
                        "unit_test_cases": self.state['test_code'] 
                    })

                    cleaned_response = CodeGenerationPlan(**llm_response)
                    self.current_code_generation_plan_list.append(cleaned_response)

                    self.error_message = ""
                    
                    break # while loop exit
                except Exception as e:
                    logger.error(f"{self.agent_name}: Error Occured at code generation: ===>{type(e)}<=== {e}.----")

                    self.error_message = e
                    self.add_message((
                        ChatRoles.USER,
                        f"{self.agent_name}: {self.error_message}"
                    ))
        
        self.add_message((
            ChatRoles.USER,
            f"{self.agent_name}: Code Generation completed!"
        ))
        self.is_code_generated = True

        return self.state

    def run_commands_node(self, state: CoderState) -> CoderState:
        """
        """
        logger.info(f"----{self.agent_name}: Executing the commands ----")
        #updating the state 
        self.update_state(state)
        self.last_visited_node = self.run_commands_node_name

        # TODO: Add logic for command execution. use self.current_code_generation
        # run one command at a time from the dictionary of commands to execute.
        # Need to add error handling prompt for this node.
        # When command execution fails llm need to re try with different commands
        # look into - Shell.execute_command, whitelisted commands for llm to pick

        #executing the commands one by one 
        try:
            for path, command in self.current_code_generation['commands_to_execute'].items():
                
                logger.info(f"----{self.agent_name}: Started executing the command: {command}, at the path: {path}.----")
    
                self.add_message((
                    ChatRoles.USER,
                    f"Started executing the command: {command}, in the path: {path}."
                ))
                execution_result=Shell.execute_command.invoke({
                    "command": command,
                    "repo_path": path
                })
                #if the command is successfully executed, run the next command 
                if execution_result[0]==False:
                    self.add_message((
                    ChatRoles.USER,
                    f"Successfully executed the command: {command}, in the path: {path}. The output of the command execution is {execution_result[1]}"
                ))
                    #if there is any error in the command execution log the error in the error_message and return the state to router by marking the has error as true and 
                    #last visited node as code generation node to generate the code and commands again, with out running the next set of commands.
                elif execution_result[0]==True:
                    
                    self.last_visited_node = self.code_generation_node_name
                    self.error_message= f"Error Occured while executing the command: {command}, in the path: {path}. The output of the command execution is {execution_result[1]}. This is the dictionary of commands and the paths where the respective command are supposed to be executed you have generated in previous run: {self.current_code_generation['commands_to_execute']}"
                    self.add_message((
                        ChatRoles.USER,
                        f"{self.agent_name}: {self.error_message}"
                    ))

                    # return {**self.state}
            
            self.has_command_execution_finished = True
        except Exception as e:
            logger.error(f"----{self.agent_name}: Error Occured while executing the commands : {str(e)}.----")

            self.error_message = f"An error occurred while processing the request: {str(e)}"

            self.add_message((
                ChatRoles.USER,
                f"{self.agent_name}: {self.error_message}"
            ))
        return {**self.state}
    
    def write_code_node(self, state: CoderState) -> CoderState:
        """
        """

        logger.info(f"----{self.agent_name}: Writing the generated code to the respective files in the specified paths ----")

        self.state = state
        self.last_visited_node = self.write_generated_code_node_name

        try:
            for generation_plan in self.current_code_generation_plan_list:
                for file_path, file_content in generation_plan.file.items():
                    logger.info(f"----{self.agent_name}: Started writing the code to the file at the path: {file_path}.----")

                    tool_execution_result = CodeFileWriter.write_generated_code_to_file.invoke(
                        {
                            "generated_code": file_content.file_code,
                            "file_path": file_path
                        }
                    )

                    # if no errors
                    if not tool_execution_result[0]:
                        logger.info(f"Successfully executed the tool at path: {file_path}. The output of the tool execution is {tool_execution_result[1]}")
                        self.add_message((
                            ChatRoles.USER,
                            f"Successfully executed the tool at path: {file_path}. The output of the tool execution is {tool_execution_result[1]}"
                        ))
                    
            self.has_code_been_written_locally = True
        except Exception as e:
            logger.error(f"{self.agent_name}: Error Occured while writing the code to the respective files : {e}.----")

            self.error_message = f"An error occurred while processing the request: {e}"

            self.add_message((
                ChatRoles.USER,
                f"{self.agent_name}: {self.error_message}"
            ))

        return self.state

    def add_license_text_node(self, state: CoderState) -> CoderState:
        """
        """
        logger.info(f"{self.agent_name}: Started adding license and copyright information to the files.")

        for generation_plan in self.current_code_generation_plan_list:
            for file_path, file_content in generation_plan.file.items():
            
                file_extension = os.path.splitext(file_path)[1]

                if len(file_extension) <= 0:
                    continue
            
                file_comment = file_content.license_comments.get(file_extension, "")

                if len(file_comment) > 0:

                    with open(file_path, 'r') as file:
                        content = file.read()

                    with open(file_path, 'w') as file:
                        file.write(f"{file_comment}\n\n{content}")

        self.is_license_text_added_to_files = True

        return self.state
        
    def download_license_node(self, state: CoderState) -> CoderState:
        """
        """
        logger.info(f"----{self.agent_name}: downloading the license file from the given url----")

        self.state = state
        self.last_visited_node = self.download_license_node_name

        license_download_result=License.download_license_file.invoke({
            "url": self.state["license_url"], 
            "file_path": os.path.join(self.state["project_path"], self.state["project_name"], "license")
        })

        self.add_message((
            ChatRoles.USER,
            f"Downloaded the license from the {self.state["license_url"]}. The output of the command execution is {license_download_result[1]}"
        ))

        self.is_license_file_downloaded = True

        return self.state

    def agent_response_node(self, state: CoderState) -> CoderState:
        """
        """
        self.state = state

        logger.info(f"{self.agent_name}: Preparing response.")

        if self.is_code_generated and self.has_code_been_written_locally and self.is_license_text_added_to_files:
            self.state['current_planned_task'].is_code_generated = True
            self.state['current_planned_task'].task_status = Status.DONE
            self.state["code_generation_plan_list"] = self.current_code_generation_plan_list
        else:
            self.state['current_planned_task'].task_status = Status.ABANDONED
        
        return self.state
