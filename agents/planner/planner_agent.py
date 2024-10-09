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
from policies.pydantic_models.constants import Status
from policies.pydantic_models.models import PlannedTask, PlannedTaskQueue
from policies.pydantic_models.planner_models import BacklogList
from prompts.planner_prompts import PlannerPrompts
from utils.logs.logging_utils import logger


class PlannerAgent(Agent[PlannerState, PlannerPrompts]):
    """
    """

    def __init__(self, llm: ChatOpenAI) -> None:

        super().__init__(
            ProjectAgents.planner.agent_id,
            ProjectAgents.planner.agent_name,
            PlannerState(),
            PlannerPrompts(),
            llm
        )

        self.error_count = 0
        self.max_retries = 3
        self.error_messages = []
        self.file_count = 0

        self.planned_backlogs: list[str] = []

        # prompts
        # backlog planner for each deliverable chain
        self.backlog_plan = self.prompts.backlog_planner_prompt | self.llm

        # detailed requirements generator chain
        self.detailed_requirements = self.prompts.detailed_requirements_prompt | self.llm

        self.segregaion_chain = self.prompts.segregation_prompt | self.llm | JsonOutputParser()

    def write_workpackages_to_files(self, output_dir: str, planned_tasks: PlannedTaskQueue) -> tuple[int, int]:
        """
        Write work packages from a dictionary to individual JSON files.

        Args:
        backlog_dict (dict): Dictionary containing work package data.
        output_dir (str): Base directory for output files.

        Returns:
        int: Number of work packages written successfully.
        """
        if len(planned_tasks) < 0:
            logger.info("----Workpackages not present----")
            return 0, self.file_count

        logger.info("----Writing workpackages to Project Docs Folder----")
        work_packages_dir = os.path.join(output_dir, "docs", "work_packages")
        os.makedirs(work_packages_dir, exist_ok=True)

        session_file_count = 0
        for planned_task in planned_tasks:
            file_name = f'work_package_{self.file_count + 1}.json'
            file_path = os.path.join(work_packages_dir, file_name)

            work_package: dict = json.loads(planned_task.description)

            try:
                with codecs.open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(work_package, file, indent=4)

                logger.info("Workpackage written to: %s", file_path)
            except UnicodeEncodeError:
                try:
                    with codecs.open(file_path, 'w', encoding='utf-8-sig') as file:
                        json.dump(work_package, file, indent=4)

                    logger.info(
                        "Workpackage written to: %s (with BOM)", file_path)
                except Exception as e:
                    logger.error(
                        "Unable to write workpackage to filepath: %s. Error: %s", file_path, str(e))

            self.file_count += 1
            session_file_count += 1
        return session_file_count, self.file_count

    def new_deliverable_check(self, state: PlannerState) -> str:
        if state['current_task'].task_status == Status.NEW:
            return "backlog_planner"
        else:
            return "requirements_developer"

    def backlog_planner(self, state: PlannerState) -> PlannerState:
        state['planned_tasks'] = PlannedTaskQueue()

        while (True):
            try:
                logger.info(
                    "----Working on building backlogs for the deliverable----")
                logger.info("Deliverable: %s",
                            state['current_task'].description)

                generated_backlogs = self.backlog_plan.invoke({
                    "deliverable": state['current_task'].description,
                    "context": state['context'],
                    "feedback": self.error_messages
                })

                if generated_backlogs.content.startswith('```json') and generated_backlogs.content.endswith('```'):
                    # Remove the ```json prefix and ``` suffix
                    cleaned_generated_backlogs = generated_backlogs.content.removeprefix(
                        '```json').removesuffix('```').strip()
                else:
                    cleaned_generated_backlogs = generated_backlogs.content

                backlogs_list = ast.literal_eval(cleaned_generated_backlogs)

                # Validate the response using Pydantic
                self.planned_backlogs = BacklogList(
                    backlogs=backlogs_list).backlogs

                self.error_count = 0
                self.error_messages = []

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

    def requirements_developer(self, state: PlannerState) -> PlannerState:
        for backlog in self.planned_backlogs:
            while (True):
                try:
                    logger.info(
                        "----Now Working on Generating detailed requirements for the backlog----")
                    logger.info("Backlog: %s", backlog)
                    response = self.detailed_requirements.invoke({
                        "backlog": backlog,
                        "deliverable": state['current_task'].description,
                        "context": state['context'],
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
                        cleaned_json = cleaned_response.removeprefix(
                            '```json').removesuffix('```').strip()
                    else:
                        # If not enclosed in code blocks, use the text as is
                        cleaned_json = cleaned_response

                    parsed_response: dict = json.loads(cleaned_json)
                    logger.info("response from planner ", parsed_response)

                    if "question" in parsed_response.keys():
                        logger.info(
                            "----Awaiting for additional information on----")
                        logger.info("Question: %s",
                                    parsed_response['question'])
                        state['current_task'].task_status = Status.AWAITING
                        state['current_task'].question = parsed_response['question']
                        return state
                    elif "description" in parsed_response.keys():
                        logger.info(
                            "----Generated Detailed requirements in JSON format for the backlog----")

                        is_function_generation_required = self.task_segregation(
                            backlog, parsed_response)
                        planned_task = PlannedTask(
                            parent_task_id=state['current_task'].task_id,
                            task_status=Status.NEW,
                            is_function_generation_required=is_function_generation_required,
                        )

                        parsed_response = {
                            "task_id": f"{planned_task.task_id}",
                            "work_package_name": f"{backlog}",
                            **parsed_response
                        }

                        planned_task.description = json.dumps(parsed_response)
                        state['planned_tasks'].add_task(planned_task)

                        logger.info("Requirements in JSON: %r",
                                    parsed_response)

                        self.error_count = 0
                        self.error_messages = []

                        break  # for while loop
                except Exception as e:
                    logger.info(
                        "Error parsing response for backlog: %s", backlog)
                    logger.error("%s", str(e))
                    self.error_count += 1

                    error_message = f"Error in generated detailed requirements format: {str(e)}, I'm using python json.loads() to convert json to dictionary so take that into consideration."
                    logger.info(
                        "Error Message fed back to LLM: %s", error_message)

                    self.error_messages.append(error_message)

                    if self.error_count >= self.max_retries:
                        logger.info("Max retries reached. Halting")
                        self.error_count = 0
                        return state

        state['current_task'].task_status = Status.INPROGRESS

        files_written, total_files_written = self.write_workpackages_to_files(
            state['project_path'], state['planned_tasks'])
        logger.info('Wrote down %d work packages into the project folder during the current session. Total files written during the current run %d',
                    files_written, total_files_written)

        return state

    def generate_response(self, state: PlannerState) -> PlannerState:
        # After attempting to handle the current task with planner chains, check the task's status.
        # If the task status is:
        # - Status.INPROGRESS: The planner has successfully prepared planned tasks.
        # - Status.AWAITING: The task is waiting for some condition or input before it can proceed.
        # - Status.NEW: An error occurred during the task execution, and it was not handled properly.
        # In the case of Status.NEW, we need to abandon the task since it could not be successfully addressed by the planner.
        if state['current_task'].task_status == Status.NEW:
            state['current_task'].task_status = Status.ABANDONED

        return state

    def parse_backlog_tasks(self, response: str) -> List[str]:

        # Split the response into lines
        lines = response.split('\n')

        # Extract tasks using regex
        tasks = []
        for line in lines:
            # Match lines that start with numbers or bullet points
            match = re.match(
                r'^(\d+\.|\*|\-)\s*\*{0,2}([^:]+)(:|\*{0,2})', line.strip())
            if match:
                task = match.group(2).strip()
                tasks.append(task)

        return tasks

    def task_segregation(self, workpackage_name: str, requirements: dict) -> bool:
        """
        """
        logger.info(f"---- Initiating segregation ----")

        try:
            llm_response = self.segregaion_chain.invoke({
                "work_package": f"{workpackage_name} \n {requirements}",
            })

            required_keys = ["taskType"]
            missing_keys = [
                key for key in required_keys if key not in llm_response]

            if missing_keys:
                raise KeyError(
                    f"Missing keys: {missing_keys} in the response. Try Again!")

            logger.info(
                f" task type  : {llm_response['taskType']} ; {llm_response['reason_for_classification']}")
        except Exception as e:
            logger.error(f"---- Error Occured at segregation: {str(e)}.----")

        return llm_response['taskType']
