"""Coder Agent
"""

from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

from langgraph.prebuilt import ToolExecutor
from langgraph.prebuilt import ToolInvocation

from langchain_core.tools import StructuredTool

from langchain_core.output_parsers import JsonOutputParser

from langchain_core.runnables.base import RunnableSequence

from agents.coder.state import CoderState

from models.constants import Status
from models.constants import ChatRoles

from models.coder import CodeGeneration

from prompts.coder import CoderPrompts

from models.coder import CoderModel

from tools.git import Git
from tools.shell import Shell
from tools.license import License
from tools.code import CodeFileWriter

from typing_extensions import Union
from typing_extensions import Literal

import pprint as pp

class CoderAgent:
    """
    """
    agent_name: str # The name of the agent

    # names of the graph node
    entry_node_name: str # The entry point of the graph
    code_generation_node_name: str 
    run_commands_node_name: str
    write_generated_code_node_name: str
    download_license_node_name: str 
    add_license_node_name: str 
    update_state_node_name: str 

    # tools used by this agent
    tools: list[StructuredTool]
    toolExecutor: ToolExecutor

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

    state: CoderState
    prompts: CoderPrompts
    current_code_generation: CodeGeneration

    llm: Union[ChatOpenAI, ChatOllama] # This is the language learning model (llm) for the Architect agent. It can be either a ChatOpenAI model or a ChatOllama model

    # chains
    code_generation_chain: RunnableSequence

    def __init__(self, llm: Union[ChatOpenAI, ChatOllama]) -> None:
        """
        """
        
        self.agent_name = "Software Programmer"

        self.entry_node_name = "entry"
        self.code_generation_node_name = "code_generation"
        self.run_commands_node_name = "run_commands"
        self.write_generated_code_node_name = "write_code"
        self.download_license_node_name = "download_license"
        self.add_license_node_name = "add_license_text"
        self.update_state_node_name = "state_update"
        
        self.tools = [
            CodeFileWriter.write_generated_code_to_file,
            Git.create_git_repo,
            Shell.execute_command
        ]
        self.toolExecutor = ToolExecutor(self.tools)

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
        
        self.state = CoderState()
        self.prompts = CoderPrompts()

        self.current_code_generation = {}

        self.llm = llm

        self.code_generation_chain = (
            self.prompts.code_generation_prompt
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

    def router(self, state: CoderState) -> str:
        """
        """

        if self.hasError:
            return self.last_visited_node
        elif self.mode == "code_generation":
            if not self.is_code_generated:
                return self.code_generation_node_name
            elif not self.is_license_file_downloaded:
                return self.download_license_node_name
            elif not self.is_license_text_added_to_files:
                return self.add_license_node_name
        
        return self.update_state_node_name
    
    def update_state(self, state: CoderState) -> CoderState:
        """
        This method updates the current state of the Architect agent with the provided state. 

        Args:
            state (ArchitectState): The new state to update the current state of the agent with.

        Returns:
            ArchitectState: The updated state of the agent.
        """
        print(f"----{self.agent_name}: Proceeding with state update----")
        
        self.state = {**state}

        return {**self.state}
    
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

        print(f"----{self.agent_name}: Initiating Graph Entry Point----")

        self.update_state(state)
        self.last_visited_node = self.entry_node_name

        if self.state['current_task'].task_status == Status.NEW:
            self.mode = "code_generation"
            self.is_code_generated = False
            self.has_command_execution_finished = False
            self.has_code_been_written_locally = False
            self.is_license_file_downloaded = False
            self.is_license_text_added_to_files = False

            self.current_code_generation = {}

        return {**self.state}
    
    def code_generation_node(self, state: CoderState) -> CoderState:
        """
        """
        print(f"----{self.agent_name}: Initiating Code Generation----")

        self.update_state(state)
        self.last_visited_node = self.code_generation_node_name

        task = self.state["current_task"]

        print(f"----{self.agent_name}: Started working on the task: {task.description}.----")
  
        self.add_message((
            ChatRoles.USER.value,
            f"Started working on the task: {task.description}."
        ))

        try:
            llm_response = self.code_generation_chain.invoke({
                "project_name": self.state['project_name'],
                "project_path": self.state['generated_project_path'],
                "requirements_document": self.state['requirements_overview'],
                "folder_structure": self.state['project_folder_strucutre'],
                "task": task.description,
                "error_message": self.error_message,
            })

            self.hasError = False
            self.error_message = ""

            required_keys = ["files_to_create", "code", "infile_license_comments", "commands_to_execute"]
            missing_keys = [key for key in required_keys if key not in llm_response]

            if missing_keys:
                raise KeyError(f"Missing keys: {missing_keys} in the response. Try Again!")

            # TODO: Need to update these to the state such that it holds the past tasks following field details along current task with no duplicates.
            # TODO: maintian class variable (local to class) to hold the current task's CodeGeneration object so that we are not gonna pass any extra
            # details to the code generation prompt - look self.current_code_generation
            self.state["code"] = llm_response['code']
            self.state["files_created"] = llm_response['files_to_create']
            self.state['infile_license_comments'] = llm_response['infile_license_comments']
            self.state['commands_to_execute'] = llm_response['commands_to_execute']

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: Code Generation completed!"
            ))

            self.is_code_generated = True
        except Exception as e:
            print(f"----{self.agent_name}: Error Occured at code generation: {str(e)}.----")

            self.hasError = True
            self.error_message = f"An error occurred while processing the request: {str(e)}"

            self.add_message((
                ChatRoles.USER.value,
                f"{self.agent_name}: {self.error_message}"
            ))
        
        pp.pp(llm_response)
        return {**self.state}

    def run_commands_node(self, state: CoderState) -> CoderState:
        """
        """

        # TODO: Add logic for command execution. use self.current_code_generation
        # run one command at a time from the dictionary of commands to execute.
        # Need to add error handling prompt for this node.
        # When command execution fails llm need to re try with different commands
        # look into - Shell.execute_command, whitelisted commands for llm to pick
        self.has_command_execution_finished = True
        
        return {**self.state}
    
    def write_code_node(self, state: CoderState) -> CoderState:
        """
        """

        # TODO: Add logic to write code to local. use self.current_code_generation.code
        # just simply run wrire_generated_code_to_local tool to achieve this
        # need to look for the case when code is empty.
        # key and value of the code dict are the parameters for tool
        self.has_code_been_written_locally = True

        return {**self.state}
    
    def download_license_node(self, state: CoderState) -> CoderState:
        """
        """

        # TODO: from state pick the license url and user download_license tool to achieve this
        self.is_license_file_downloaded = True

        return {**self.state}
    
    def add_license_text_node(self, state: CoderState) -> CoderState:
        """
        """

        # TODO: Need to work on a logic to achieve this
        # use self.state['infile_license_text]
        # and only loop to add to the filepaths that self.current_code_generation.code.keys() has
        # or else there is chance for duplicating the license text to already written files.
        self.is_license_text_added_to_files = True

        return {**self.state}