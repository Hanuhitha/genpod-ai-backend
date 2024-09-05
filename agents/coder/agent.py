"""Coder Agent
"""
import os
from typing import Literal

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import ChatOpenAI

from agents.agent.agent import Agent
from agents.coder.state import CoderState
from configs.project_config import ProjectAgents
from models.coder import CodeGenerationPlan
from models.constants import ChatRoles, Status
from prompts.coder import CoderPrompts
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
    run_commands_node_name: str
    write_generated_code_node_name: str
    download_license_node_name: str 
    add_license_node_name: str 
    update_state_node_name: str 

    mode: Literal["code_generation"]

    # local state of this class which is not exposed
    # to the graph state
    hasError: bool
    is_code_generated: bool
    has_command_execution_finished: bool
    has_code_been_written_locally: bool
    is_code_written_to_local: bool
    is_license_file_downloaded: bool
    is_license_text_added_to_files: bool
    hasPendingToolCalls: bool

    last_visited_node: str
    error_message: str
    
    track_add_license_txt: list[str]

    current_code_generation: CodeGenerationPlan

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
        self.run_commands_node_name = "run_commands"
        self.write_generated_code_node_name = "write_code"
        self.download_license_node_name = "download_license"
        self.add_license_node_name = "add_license_text"
        self.update_state_node_name = "state_update"

        self.mode = ""

        self.hasError = False
        self.is_code_generated = False
        self.has_command_execution_finished = False
        self.has_code_been_written_locally = False
        self.is_license_file_downloaded = False
        self.is_license_text_added_to_files = False
        self.hasPendingToolCalls = False

        self.last_visited_node = self.code_generation_node_name
        self.error_message = ""

        self.current_code_generation = CodeGenerationPlan()

        self.track_add_license_txt = []
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

        if self.hasError:
            return self.last_visited_node
        elif self.mode == "code_generation":
            if not self.is_code_generated:
                return self.code_generation_node_name
            # elif not self.has_command_execution_finished:
            #     return self.run_commands_node_name
            elif not self.has_code_been_written_locally:
                return self.write_generated_code_node_name
            elif not self.is_license_file_downloaded:
                return self.download_license_node_name
            elif not self.is_license_text_added_to_files:
                return self.add_license_node_name
        
        return self.update_state_node_name

    def update_state_code_generation(self, current_cg: CodeGenerationPlan) -> None:
        """
        """

        # if self.state['files_created'] is None:
        #     self.state['files_created'] = current_cg['files_to_create']
        # else:
        #     new_list = [item for item in current_cg['files_to_create'] if item not in self.state['files_created']]

        #     self.state['files_created'] += new_list
        
        if self.state['code'] is None:
            self.state["code"] = current_cg['code']
        else:
            state_ifc = current_cg['code'].copy()

            for key in state_ifc:
                if key in self.state['code']:
                    del current_cg['code'][key]

        # if self.state['infile_license_comments'] is None:
        #     self.state['infile_license_comments'] = current_cg['infile_license_comments']
        # else:
        #     state_ifc = current_cg['infile_license_comments'].copy()

        #     for key in state_ifc:
        #         if key in self.state['infile_license_comments']:
        #             del current_cg['infile_license_comments'][key]
            
        #     self.state['infile_license_comments'].update(current_cg['infile_license_comments'])

        # if self.state['commands_to_execute'] is None:
        #     self.state['commands_to_execute'] = current_cg['commands_to_execute']
        # else:
        #     self.state['commands_to_execute'].update(current_cg['commands_to_execute'])

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
        self.state = {**state}

        self.last_visited_node = self.entry_node_name

        if self.state['current_planned_task'].task_status == Status.NEW:
            self.mode = "code_generation"
            self.is_code_generated = False
            self.has_command_execution_finished = False
            self.has_code_been_written_locally = False
            self.is_license_text_added_to_files = False

            self.current_code_generation = CodeGenerationPlan()

        return self.state
    
    def code_generation_node(self, state: CoderState) -> CoderState:
        """
        """
        logger.info(f"----{self.agent_name}: Initiating Code Generation----")

        self.state = {**state}
        self.last_visited_node = self.code_generation_node_name

        task = self.state["current_planned_task"]

        logger.info(f"----{self.agent_name}: Started working on the task: {task.description}.----")
  
        self.add_message((
            ChatRoles.USER,
            f"Started working on the task: {task.description}."
        ))

        try:
            
            # TODO: Figure out a proper way to write the condition(if condition)
            if task.is_function_generation_required:
                llm_response = self.code_generation_chain.invoke({
                    "project_name": self.state['project_name'],
                    "project_path": os.path.join(self.state['project_path'], self.state['project_name']),
                    "requirements_document": self.state['requirements_document'],
                    "folder_structure": self.state['project_folder_strucutre'],
                    "task": task.description,
                    "error_message": self.error_message,
                    "unit_test": self.state['test_code'],
                    "functions_skeleton": self.state['functions_skeleton']
                })
            else:
                 llm_response = self.code_generation_chain.invoke({
                    "project_name": self.state['project_name'],
                    "project_path": os.path.join(self.state['project_path'], self.state['project_name']),
                    "requirements_document": self.state['requirements_document'],
                    "folder_structure": self.state['project_folder_strucutre'],
                    "task": task.description,
                    "error_message": self.error_message,
                    "unit_test":"No UnitTests",
                    "functions_skeleton":"No_skeleton"
                })

            self.hasError = False
            self.error_message = ""

            # required_keys = ["files_to_create", "code", "infile_license_comments", "commands_to_execute"]
            required_keys = ["code"]
            
            missing_keys = [key for key in required_keys if key not in llm_response]

            if missing_keys:
                raise KeyError(f"Missing keys: {missing_keys} in the response. Try Again!")

            # TODO: Need to update these to the state such that it holds the past tasks following field details along current task with no duplicates.
          
            self.update_state_code_generation(llm_response)

            # TODO: maintian class variable (local to class) to hold the current task's CodeGenerationPlan object so that we are not gonna pass any extra
            # details to the code generation prompt - look self.current_code_generation

            self.current_code_generation["code"] = llm_response['code']
            # self.current_code_generation["files_created"] = llm_response['files_to_create']
            # self.current_code_generation['infile_license_comments'] = llm_response['infile_license_comments']
            # self.current_code_generation['commands_to_execute'] = llm_response['commands_to_execute']

            self.add_message((
                ChatRoles.USER,
                f"{self.agent_name}: Code Generation completed!"
            ))

            self.is_code_generated = True
        except Exception as e:
            logger.error(f"----{self.agent_name}: Error Occured at code generation: ===>{type(e)}<=== {str(e)}.----")

            self.hasError = True
            self.error_message = f"An error occurred while processing the request: {str(e)}"

            self.add_message((
                ChatRoles.USER,
                f"{self.agent_name}: {self.error_message}"
            ))
        
        return {**self.state}

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
                    
                    self.hasError=True
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

            self.hasError = True
            self.error_message = f"An error occurred while processing the request: {str(e)}"

            self.add_message((
                ChatRoles.USER,
                f"{self.agent_name}: {self.error_message}"
            ))
        return {**self.state}
    
    def write_code_node(self, state: CoderState) -> CoderState:
        """
        """
        # TODO: Add logic to write code to local. use self.current_code_generation.code
        # just simply run wrire_generated_code_to_local tool to achieve this
        # need to look for the case when code is empty.
        # key and value of the code dict are the parameters for tool

        logger.info(f"----{self.agent_name}: Writing the generated code to the respective files in the specified paths ----")

        self.state = {**state}
        self.last_visited_node = self.write_generated_code_node_name

        try:
            for path, code in self.current_code_generation['code'].items():
                
                logger.info(f"----{self.agent_name}: Started writing the code to the file at the path: {path}.----")
    
                self.add_message((
                    ChatRoles.USER,
                    f"Started writing the code to the file in the path: {path}."
                ))
                execution_result=CodeFileWriter.write_generated_code_to_file.invoke({
                    "generated_code": code,
                    "file_path": path
                })

                #if the code successfully stored in the specifies path, write the next code in the file
                if execution_result[0]==False:
                    self.add_message((
                    ChatRoles.USER,
                    f"Successfully executed the command: , in the path: {path}. The output of the command execution is {execution_result[1]}"
                ))
                    
                    #if there is any error in writing the code to the files log the error in the error_message and return the state to router by marking the has error as true and 
                    #last visited node as code generation node to generate the code and, with out running the next set of writing the files.
                elif execution_result[0]==True:
                    
                    self.hasError=True
                    self.last_visited_node = self.code_generation_node_name
                    self.error_message= f"Error Occured while writing the code in the path: {path}. The output of writing the code to the file is {execution_result[1]}."
                    self.add_message((
                    ChatRoles.USER,
                    f"{self.agent_name}: {self.error_message}"
                ))

            self.has_code_been_written_locally = True
        except Exception as e:
            logger.error(f"----{self.agent_name}: Error Occured while writing the code to the respective files : {str(e)}.----")

            self.hasError = True
            self.error_message = f"An error occurred while processing the request: {str(e)}"

            self.add_message((
                ChatRoles.USER,
                f"{self.agent_name}: {self.error_message}"
            ))

        return self.state
    
    def download_license_node(self, state: CoderState) -> CoderState:
        """
        """
        logger.info(f"----{self.agent_name}: downloading the license file from the given location {self.state['license_url']} ----")

        self.update_state(state)
        self.last_visited_node = self.download_license_node_name

        license_download_result=License.download_license_file.invoke({
            "url": self.state["license_url"], 
            "file_path": os.path.join(self.state["project_path"], self.state["project_name"], "license")
        })

        self.add_message((
                    ChatRoles.USER,
                    f"Downloaded the license from the {self.state["license_url"]}. The output of the command execution is {license_download_result[1]}"
                ))

        # TODO: from state pick the license url and user download_license tool to achieve this

        self.is_license_file_downloaded = True

        return self.state
    
    def add_license_text_node(self, state: CoderState) -> CoderState:
        """
        """

        # TODO: Need to work on a logic to achieve this
        # use self.state['infile_license_text]
        # and only loop to add to the filepaths that self.current_code_generation.code.keys() has
        # or else there is chance for duplicating the license text to already written files.
        logger.info("Edited the license of the files")

        for path, code in self.current_code_generation['code'].items():
            
            if path not in self.track_add_license_txt:
                file_extension = os.path.splitext(path)[1]

                if len(file_extension) <= 0:
                    continue
            
                file_comment = "" #self.state['infile_license_comments'].get(file_extension, "")

                if len(file_comment) > 0:

                    with open(path, 'r') as file:
                        content = file.read()

                    with open(path, 'w') as file:
                        file.write(file_comment + "\\n" + content)
                    
                    self.track_add_license_txt.append(path)

        self.is_license_text_added_to_files = True
        self.state['current_planned_task'].is_code_generate = True
        self.state['current_planned_task'].task_status = Status.DONE

        return self.state
    