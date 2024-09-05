import ast
import codecs
import json
import os
import re
from typing import List

from langchain_core.output_parsers.json import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from agents.agent.agent import Agent
from agents.planner.planner_state import PlannerState
from configs.project_config import ProjectAgents
from models.constants import Status
from models.models import Task
from models.planner import BacklogList
from prompts.planner import PlannerPrompts
# TODO: move these prompts planner prompts
from prompts.segregation import SegregatorPrompts
from utils.logs.logging_utils import logger


class PlannerAgent(Agent[PlannerState, PlannerPrompts]):
    """
    """
    
    def __init__(self, llm: ChatOpenAI):
        
        super().__init__(
            ProjectAgents.planner.agent_id,
            ProjectAgents.planner.agent_name,
            PlannerState(),
            PlannerPrompts(),
            llm
        )

        # backlog planner for each deliverable chain
        self.backlog_plan = self.prompts.backlog_planner_prompt | self.llm
        
        # detailed requirements generator chain
        self.detailed_requirements = self.prompts.detailed_requirements_prompt | self.llm

        self.segregaion_chain= SegregatorPrompts.segregation_prompt| self.llm | JsonOutputParser()

        self.current_task : Task = None

        self.error_count = 0
        self.max_retries = 3
        self.error_messages = []
        self.backlog_requirements = {}
        self.file_count = 0

    def write_workpackages_to_files(self, backlog_dict, output_dir) -> tuple[int, int]:
        """
        Write work packages from a dictionary to individual JSON files.

        Args:
        backlog_dict (dict): Dictionary containing work package data.
        output_dir (str): Base directory for output files.

        Returns:
        int: Number of work packages written successfully.
        """
        if not backlog_dict:
            logger.info("----Workpackage not present----")
            return 0, self.file_count

        logger.info("----Writing Workpackages to Project Docs Folder----")
        work_packages_dir = os.path.join(output_dir, "docs", "work_packages")
        os.makedirs(work_packages_dir, exist_ok=True)

        session_file_count = 0
        for key, value in backlog_dict.items():
            work_package = {'work_package_name': key, **value}
            file_name = f'work_package_{self.file_count + 1}.json'
            file_path = os.path.join(work_packages_dir, file_name)

            try:
                with codecs.open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(work_package, file, indent=4)
                logger.info("Workpackage written to: %s", file_path)
                self.file_count += 1
                session_file_count += 1
            except UnicodeEncodeError:
                try:
                    with codecs.open(file_path, 'w', encoding='utf-8-sig') as file:
                        json.dump(work_package, file, indent=4)
                    logger.info("Workpackage written to: %s (with BOM)", file_path)
                    self.file_count += 1
                    session_file_count += 1
                except Exception as e:
                    logger.error("Unable to write workpackage to filepath: %s. Error: %s", file_path, str(e))

        return session_file_count, self.file_count
    
    def new_deliverable_check(self, state: PlannerState):
        # self.current_task = {x:config['configurable'][x] for x in ['description','task_status','additional_info','question']}
        # self.current_task = state.new_task
        # if config['configurable']['task_status'] == Status.NEW.value:
        if state['current_task'].task_status == Status.NEW:
            return "backlog_planner"
        else:
            return "requirements_developer"

    def backlog_planner(self, state: PlannerState):
        while(True):
            try:
                logger.info("----Working on building backlogs for the deliverable----")
                logger.info("Deliverable: %s", state['current_task'].description)

                generated_backlogs = self.backlog_plan.invoke({
                    "deliverable": state['current_task'].description, 
                    "context": state['current_task'].additional_info, 
                    "feedback": self.error_messages
                })

                if generated_backlogs.content.startswith('```json') and generated_backlogs.content.endswith('```'):
                    # Remove the ```json prefix and ``` suffix
                    cleaned_generated_backlogs = generated_backlogs.content.removeprefix('```json').removesuffix('```').strip()
                else:
                    cleaned_generated_backlogs = generated_backlogs.content

                backlogs_list = ast.literal_eval(cleaned_generated_backlogs)
                
                # Validate the response using Pydantic
                validated_backlogs = BacklogList(backlogs=backlogs_list)
                
                self.error_count = 0
                self.error_messages = []

                # Update the state with the validated backlogs
                state['deliverable'] = state['current_task'].description
                state['backlogs'] = validated_backlogs.backlogs

                # Extend the planned_task_map with the new backlogs
                state['planned_task_map'] = {state['deliverable']: {wp: False for wp in state['backlogs']}}
                
                return state
            except (ValidationError, ValueError, SyntaxError) as e:
                self.error_count += 1
                error_message = f"Error generating backlogs: {str(e)}"
                
                logger.error(error_message)
                self.error_messages.append(error_message)
                
                if self.error_count >= self.max_retries:
                    logger.info("Max retries reached. Halting")
                    self.error_count = 0
                    return state

    def requirements_developer(self, state: PlannerState):        
        state['planned_task_requirements'] = {}
        ptm = {}
        for backlog in state['planned_task_map'][state['current_task'].description]:
            while(True):
                try:
                    logger.info("----Now Working on Generating detailed requirements for the backlog----")
                    logger.info("Backlog: %s", backlog)
                    response = self.detailed_requirements.invoke({
                        "backlog": backlog, 
                        "deliverable": state['deliverable'], 
                        "context": state['current_task'].additional_info, 
                        "feedback": self.error_messages
                    })

                    # Let's clean the response to remove json prefix that llm sometimes appends to the actual text
                    # Strip whitespace from the beginning and end
                    cleaned_response = response.content.strip()
                    # Remove single-line comments
                    # cleaned_response = re.sub(r'//.*$', '', cleaned_response, flags=re.MULTILINE)
                    # Remove multi-line comments
                    # cleaned_response = re.sub(r'/\*.*?\*/', '', cleaned_response, flags=re.DOTALL)
                    
                    # Check if the text starts with ```json and ends with ```
                    if cleaned_response.startswith('```json') and cleaned_response.endswith('```'):
                        # Remove the ```json prefix and ``` suffix
                        cleaned_json = cleaned_response.removeprefix('```json').removesuffix('```').strip()
                    else:
                        # If not enclosed in code blocks, use the text as is
                        cleaned_json = cleaned_response

                    parsed_response: dict = json.loads(cleaned_json)
                    logger.info("response from planner ", parsed_response)

                    if "question" in parsed_response.keys():
                        logger.info("----Awaiting for additional information on----")
                        logger.info("Question: %s", parsed_response['question'])
                        state['current_task'].task_status = Status.AWAITING
                        state['current_task'].question = parsed_response['question']
                        return state
                    elif "description" in parsed_response.keys():
                        logger.info("----Generated Detailed requirements in JSON format for the backlog----")
                        # logger.info("Requirements in JSON: %r", parsed_response)

                        # adding the segregation node to  check if the generated requirements require to 
                        is_function_generation_required = self.task_segregation(backlog, parsed_response)
                        parsed_response['is_function_generation_required'] = is_function_generation_required
                        state['planned_task_requirements'][backlog] = parsed_response
                        state['planned_task_map'][state['current_task'].description][backlog] = is_function_generation_required
                        logger.info("Requirements in JSON: %r", parsed_response)

                        self.error_count = 0
                        self.error_messages = []
                        break
                except Exception as e:
                    logger.info("Error parsing response for backlog: %s", backlog)
                    logger.error("%s", str(e))
                    self.error_count += 1
                    
                    error_message = f"Error in generated detailed requirements format: {str(e)}, I'm using python json.loads() to convert json to dictionary so take that into consideration."
                    logger.info("Error Message fed back to LLM: %s", error_message)
                    
                    self.error_messages.append(error_message)
                    
                    if self.error_count >= self.max_retries:
                        logger.info("Max retries reached. Halting")
                        self.error_count = 0
                        return state
                    
        """Uncomment the below line to call coder on each workpackage created for the deliverable. Currently coder is not implemented yet so we will try to build workpackages for eacg deliverable using the Done mode."""
        # state['current_task'].task_status = Status.INPROGRESS
        state['current_task'].task_status = Status.DONE

        files_written, total_files_written = self.write_workpackages_to_files(state['planned_task_requirements'], state['project_path'])
        logger.info('Wrote down %d work packages into the project folder during the current session. Total files written during the current run %d', files_written, total_files_written)
        return state

    def generate_response(self, state: PlannerState):
        if state['current_task'].task_status == Status.DONE:
            # ----when calling Coder----
            response = Task(description=state['current_task'].description, task_status=Status.INPROGRESS, additional_info='',question='')
            # ----When recursively calling planner on each deliverable----
            # response = Task(description="All Backlogs for the deliverable is successfully generated proceed further", task_status=Status.DONE.value, additional_info=state['current_task'].additional_info,question='')
        elif state['current_task'].task_status == Status.AWAITING:
            response = state['current_task']
        else:
            response = Task(description=state['current_task'].description, task_status=Status.ABANDONED, additional_info=state['current_task'].additional_info, question=state['current_task'].question)

        if state['response'] is None:
            state["response"] = [response]
        else:
            state["response"].append(response)

        return state
    
    def parse_backlog_tasks(self, response: str) -> List[str]:

        # Split the response into lines
        lines = response.split('\n')
        
        # Extract tasks using regex
        tasks = []
        for line in lines:
            # Match lines that start with numbers or bullet points
            match = re.match(r'^(\d+\.|\*|\-)\s*\*{0,2}([^:]+)(:|\*{0,2})', line.strip())
            if match:
                task = match.group(2).strip()
                tasks.append(task)
        
        return tasks
    
    def task_segregation(self, workpackage_name:str, requirements:str) -> bool:
        """
        """
        logger.info(f"---- Initiating segregation ----")

        try:
            llm_response = self.segregaion_chain.invoke({
                "work_package": workpackage_name +"/n" + str(requirements)
            })

            self.hasError = False
            self.error_message = ""
            required_keys = ["taskType"]
            missing_keys = [key for key in required_keys if key not in llm_response]

            if missing_keys:
                raise KeyError(f"Missing keys: {missing_keys} in the response. Try Again!")
            
            # Checking if the segregation agent generated tasktype

            logger.info(f" task type  : {llm_response['taskType']} ; {llm_response['reason_for_classification']}")
        except Exception as e:
            logger.error(f"---- Error Occured at segregation: {str(e)}.----")

            self.hasError = True
            self.error_message = f"An error occurred while processing the request: {str(e)}"
        
        return llm_response['taskType']
