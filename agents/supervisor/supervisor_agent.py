import ast
import json
from typing import TYPE_CHECKING, Dict, List, Tuple
import time
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from configs.database import get_client_local_db_file_path
from database.database import Database

from agents.agent.agent import Agent
from agents.supervisor.supervisor_state import SupervisorState
from agents.supervisor.classifier import SupervisorClassifier
from configs.project_config import ProjectAgents
from main import USER_ID
from models.constants import ChatRoles, PStatus, Status
from models.models import (PlannedTask, PlannedTaskQueue, RequirementsDocument,
                           Task, TaskQueue)
from models.supervisor import QueryList
from prompts.supervisor import SupervisorPrompts
from utils.fuzzy_rag_cache import FuzzyRAGCache
from utils.logs.logging_utils import logger

# to avoid circular dependency
if TYPE_CHECKING:
    from genpod.team import TeamMembers  # Adjust import path as needed


class SupervisorAgent(Agent[SupervisorState, SupervisorPrompts]):

    team: 'TeamMembers'
    previous_project_status: PStatus

    def __init__(self, llm: ChatOpenAI) -> None:

        super().__init__(
            ProjectAgents.supervisor.agent_id,
            ProjectAgents.supervisor.agent_name,
            SupervisorState(),
            SupervisorPrompts(),
            llm
        )
        self.team = None
        self.previous_project_status = PStatus.NONE

        # TODO - LOW: has to be moved to RAG agent
        self.rag_cache = FuzzyRAGCache()
        self.rag_cache_building = ''

        # TODO: NEED to check when this field has to be updated back and forth
        self.is_test_generator_agent_called: bool = False

        # TODO - LOW: has to be moved to RAG agent
        # Represents whether rag cache was created or not. single time update
        self.is_rag_cache_created: bool = False

        self.is_initial_additional_info_ready: bool = False  # single time update. set once
        self.are_requirements_prepared: bool = False  # single time update

        # Indicates whether any planned tasks are currently in progress.
        # This flag is managed by the supervisor:
        # - Set to True when the planner breaks down larger tasks into smaller planned tasks.
        # - Set to False when the planned tasks list is empty.
        # The flag is used to control a loop that operates while planned tasks are being created and processed.
        self.are_planned_tasks_in_progress: bool = False

        self.calling_agent: str = ""
        self.called_agent: str = ""

        self.responses: Dict[str, List[Tuple[str, Task]]] = {}
        self.tasks = []

        # prompts
        self.project_init_questionaire = self.prompts.init_rag_questionaire_prompt | self.llm
        self.evaluation_chain = self.prompts.follow_up_questions | self.llm

        self.classifier = SupervisorClassifier(self.llm)

    def setup_team(self, team: 'TeamMembers') -> None:
        """
        Sets up the team for the project.

        This method assigns the provided team object to the instance's team attribute.

        Args:
            team (TeamMembers): An instance of the TeamMembers class, which represents
                                the team to be assigned.

        Returns:
            None: This method does not return any value.
        """

        self.team = team
        self.classifier.set_agents(team=team)

    # TODO - LOW: has to be moved to RAG agent
    def build_rag_cache(self, query: str) -> tuple[list[str], str]:
        """
        takes the user requirements as an input and prepares a set of queries(anticipates the questions)
        that team members might get back with and prepares the answers for them and hold them in the
        rag cache.

        returns list of queries and response to the queries.
        """
        # I need to build a rag_cache during kick_off with answers to questions about requirements.
        context = ''
        count = 3

        # Prepare questionaire for rag cache
        while (count > 0):
            try:
                req_queries = self.project_init_questionaire.invoke(
                    {'user_prompt': query, 'context': context})
                req_queries = ast.literal_eval(req_queries.content)
                validated_requirements_queries = QueryList(
                    req_queries=req_queries)
                break
            except (ValidationError, ValueError, SyntaxError) as e:
                context += str(e)
                count = count-1

        if validated_requirements_queries.req_queries:
            final_response = ''

            for req_query in validated_requirements_queries.req_queries:
                result = self.rag_cache.get(req_query)

                if result is not None:
                    logger.debug("Cache hit for query: %s", req_query)
                    rag_response = result
                else:
                    logger.debug("Cache miss for query: %s", req_query)
                    logger.info(
                        f'----------{self.team.rag.member_name} Agent Called to Query----------')
                    logger.info("Query: %s", req_query)

                    result = self.team.rag.invoke({
                        'question': req_query,
                        'max_hallucination': 3
                    })
                    rag_response = result['generation']
                    self.rag_cache.add(req_query, rag_response)

                    logger.info(
                        f"'----------{self.team.rag.member_name} Agent Response----------")
                    logger.info(
                        f"{self.team.rag.member_name} Response: %s", rag_response)

                    if result['query_answered'] is True:
                        # Evaluate the RAG response
                        evaluation_result = self.evaluation_chain.invoke({
                            'user_query': req_query,
                            'initial_rag_response': rag_response}
                        )

                        if evaluation_result.content.startswith("COMPLETE"):
                            final_response += f"Question: {req_query}\nAnswer: {rag_response}\n\n"
                        elif evaluation_result.content.startswith("INCOMPLETE"):
                            follow_up_query = evaluation_result.content.split(
                                "Follow-up Query:")[1].strip()

                            logger.info(
                                "----------Follow-up query needed----------")
                            logger.info("Follow-up: %s", follow_up_query)

                            # Ask the follow-up query to the RAG agent
                            follow_up_result = self.team.rag.invoke({
                                'question': follow_up_query,
                                'max_hallucination': 3
                            })

                            follow_up_response = follow_up_result['generation']
                            self.rag_cache.add(
                                follow_up_query, follow_up_response)

                            final_response += f"Question: {req_query}\nInitial Answer: {rag_response}\nFollow-up Question: {follow_up_query}\nFollow-up Answer: {follow_up_response}\n\n"
                        else:
                            logger.info("Unexpected evaluation result format")

                            final_response += f"Question: {req_query}\nAnswer: {rag_response}\n\n"

            return (validated_requirements_queries.req_queries, final_response)
        else:
            return ([], 'Failed to initialize project')

    def instantiate_state(self, state: SupervisorState) -> SupervisorState:
        """
        Initializes the state for the supervisor agent.

        This method sets up the initial state for the supervisor agent, ensuring all necessary
        attributes are initialized. It also checks if the team has been set up before proceeding.

        Args:
            state (SupervisorState): The state object to be initialized.

        Returns:
            SupervisorState: The initialized state object.

        Raises:
            ValueError: If the team has not been initialized.
        """

        # TODO: New fields has been added to super state add them here.

        if self.team is None:
            raise ValueError(
                f"Error: The team for '{self.agent_name}' has not been initialized. "
                f"Current value of 'self.team': {self.team}. "
                "Please ensure that the 'set_team' method has been called on the supervisor agent "
                "to initialize the team before attempting this operation."
            )

        # initialize supervisor state
        state['project_name'] = ""
        state['project_status'] = PStatus.RECEIVED
        state['microservice_name'] = ""
        state['tasks'] = TaskQueue()
        state['current_task'] = Task()
        # state['current_agent'] = "RAG agent"
        state['requirements_document'] = RequirementsDocument()
        state['messages'] = [
            (
                ChatRoles.USER,
                state['original_user_input']
            ),
            (
                ChatRoles.SYSTEM,
                f'A new project with the following details has been received from the user: {state["original_user_input"]}'
            ),
            (ChatRoles.AI, "The project has been received by the team, and now the RAG (team member) needs to gather more detailed information about the project. Initial user input is often too vague to begin work, which can lead to generic results. To ensure clarity on user expectations, RAG retrieves relevant information from standardized documents. This helps provide the team with the necessary context to deliver more efficient and accurate outputs.")
        ]
        state['human_feedback'] = []
        state['rag_cache_queries'] = []
        state['is_rag_query_answered'] = False
        state['rag_retrieval'] = ''
        state['agents_status'] = ''
        state['current_planned_task'] = PlannedTask()
        state['planned_tasks'] = PlannedTaskQueue()
        state['planned_task_map'] = {}
        state['planned_task_requirements'] = {}
        state['project_folder_strucutre'] = ''
        state['code'] = ''
        state['files_created'] = []
        state['infile_license_comments'] = {}
        state['commands_to_execute'] = {}
        state['visited_agents'] = []
        state['current_agent'] = "None"

        self.responses = {member.member_id: []
                          for member in self.team.get_team_members_as_list()}

        logger.info(
            f"Supervisor state has been initialized successfully. current supervisor state: {state}")

        return state

    def call_rag(self, state: SupervisorState) -> SupervisorState:
        """
            Gathers the required information from vector DB.
        """

        logger.info(f"{self.team.rag.member_name} has been called.")
        self.called_agent = self.team.rag.member_id
        state['current_agent'] = self.team.rag.member_name

        # TODO - LOW: has to be moved to RAG agent
        # check if rag cache was ready if not prepare one
        if not self.is_rag_cache_created:
            logger.info(
                f"{self.team.rag.member_name}: creating the RAG cache.")

            # TODO - MEDIUM: Define a proper data structure for holding the RAG queries and answers together.
            # Reason: self.rag_cache_building is a string that holds all the queries and answers.
            # When a cache hit occurs, we use self.rag_cache_building as a response. This can provide too much
            # information, which might be unnecessary at that moment or might include irrelevant information.
            # SIDE EFFECTS:
            # 1. LLMs might hallucinate.
            # 2. Increases the usage of prompt tokens.

            # TODO - MEDIUM: Set a cache size limit.
            # Potential issue: As the cache grows, performance issues may arise, significantly slowing down the
            # application since we are dealing with strings and performing many string comparisons.
            # Solution: Choose and implement algorithms like LRU (Least Recently Used) or LFU (Least Frequently Used).
            state['rag_cache_queries'], self.rag_cache_building = self.build_rag_cache(
                state['original_user_input'])
            self.is_rag_cache_created = True
            logger.info(
                f"{self.team.rag.member_name}: The RAG cache has been created. The following queries were used during the process: {state['rag_cache_queries']}")

        question = state['current_task'].question
        try:

            # Check RAG cache for the information first
            result = self.rag_cache.get(question)
            if result is not None:
                logger.debug("Cache hit for query: \n%s", question)

                state['is_rag_query_answered'] = True
            else:
                logger.debug("Cache miss for query: \n%s", question)

                start_time = time.time()

                additional_info = self.team.rag.invoke({
                    'question': question,
                    'max_hallucination': 3
                })
                end_time = time.time()
                duration = end_time - start_time

                self.save_execution_time(
                    state['current_task'].task_id, start_time, end_time, duration, self.team.rag.member_name)

                result = additional_info['generation']
                state['is_rag_query_answered'] = additional_info['query_answered']
                self.rag_cache.add(question, result)

            logger.info(
                f"{self.team.rag.member_name} is ready with a response for the query: {question}")
        except Exception as e:
            raise (e)

        if state['project_status'] == PStatus.NEW:
            if state['current_task'].task_status == Status.NEW:
                logger.info(
                    f"{self.team.rag.member_name}: Received user requirements and gathering additional information.")
                state['messages'] += [
                    (
                        ChatRoles.AI,
                        f"{self.team.rag.member_name}: Received user requirements and gathering additional information to begin the project."
                    )
                ]

                state['current_task'].additional_info = result + \
                    "\n" + self.rag_cache_building
                state['current_task'].task_status = Status.DONE
                self.is_initial_additional_info_ready = True
                state['rag_retrieval'] = result + \
                    "\n" + self.rag_cache_building
                state['agents_status'] = f'{self.team.rag.member_name} completed'
                self.responses[self.team.rag.member_id].append(
                    ("Returned from RAG database", state['current_task']))

                return state
        elif state['project_status'] == PStatus.MONITORING:
            if state['current_task'].task_status == Status.AWAITING:

                logger.info(
                    f"{self.team.rag.member_name}: Received a query from team members and preparing an answer.")

                state['messages'] += [
                    (
                        ChatRoles.AI,
                        f"{self.team.rag.member_name}: Received a query from team members and preparing an answer."
                    )
                ]

                # TODO - MEDIUM: We are adding strings like `RAG_Response:` and using this word for conditional checks in a few places.
                # problem is performance degradation: the application slows down because we are searching for a small string in a very large
                # string.
                state['current_task'].task_status = Status.RESPONDED
                state['current_task'].additional_info += "\nRAG_Response:\n" + result
                state['rag_retrieval'] += result
                state['agents_status'] = f'{self.team.rag.member_name} completed'
                self.responses[self.team.rag.member_id].append(
                    ("Returned from RAG database serving a query", state['current_task']))
                # state['messages'] += [
                #     (ChatRoles.AI, f'{state['visited_agents'][-2]} can be called back now')]
            return {**state}

        return {**state}

    def call_architect(self, state: SupervisorState) -> SupervisorState:
        """
        Prepares requirements document and answers queries for the team members.
        """

        logger.info(f"{self.team.architect.member_name} has been called.")
        self.called_agent = self.team.architect.member_id
        state['current_agent'] = self.team.architect.member_name

        if state['project_status'] == PStatus.INITIAL:
            logger.info(
                f"{self.team.architect.member_name}: Started  working on requirements document.")

            architect_result = self.team.architect.invoke({
                'current_task': state['current_task'],
                'project_status': state['project_status'],
                'original_user_input': state['original_user_input'],
                'project_path': state['project_path'],
                'user_requested_standards': state['current_task'].additional_info,
                'license_text': state['license_text'],
                'messages': []
            })

            # if the task_status is done that mean architect has generated all the required information for team
            if architect_result['current_task'].task_status == Status.DONE:
                self.are_requirements_prepared = True
                state['current_task'] = architect_result['current_task']
                state['agents_status'] = f'{self.team.architect.member_name} completed'
                self.responses[self.team.architect.member_id].append(
                    ("Returned from Architect", architect_result['tasks']))
                state['tasks'].add_tasks(architect_result['tasks'])
                state['requirements_document'] = architect_result['requirements_document']
                state['project_name'] = architect_result['project_name']
                state['microservice_name'] = architect_result['project_name']
                state['project_folder_strucutre'] = architect_result['project_folder_structure']

                return state
            elif architect_result['current_task'].task_status == Status.AWAITING:
                state['current_task'] = architect_result['current_task']
                state['agents_status'] = f'{self.team.architect.member_name} Awaiting'
                self.responses[self.team.architect.member_id].append(
                    ("Returned from Architect with a question:", architect_result['current_task'].question))

                return state
        elif state['project_status'] == PStatus.MONITORING:
            # Need to query Architect to get additional information for another agent which will be present in called agent and that will never be updated when returning
            logger.info("----------Querying Architect----------")

            architect_result = self.team.architect.invoke({
                'current_task': state['current_task'],
                'project_status': state['project_status'],
                'original_user_input': state['original_user_input'],
                'project_path': state['project_path'],
                'user_requested_standards': state['current_task'].additional_info,
                'license_text': state['license_text'],
                'messages': []
            })

            logger.info("----------Response from Architect Agent----------")
            logger.info("Architect Response: %r",
                        architect_result['current_task'])

            # TODO: make architect to update the task_status to RESPONDED when done. else keep it awaiting means architect has no answer for the question.
            if architect_result['query_answered'] is True:
                state['agents_status'] = f'{self.team.architect.member_name} completed'
                self.responses[self.team.architect.member_id].append(
                    ("Returned from Architect serving a Query", architect_result['current_task']))
                state['current_task'] = architect_result['current_task']

                return state
            elif state['is_rag_query_answered'] is False and architect_result['query_answered'] is False:
                # Additional Human input is needed
                state['current_task'] = architect_result['current_task']
                state['project_status'] = PStatus.HALTED
        else:
            state['current_agent'] = 'None'

        return state

    def call_coder(self, state: SupervisorState) -> SupervisorState:
        """
        """
        # state['messages'] += [(
        #     ChatRoles.AI,
        #     'Calling Coder Agent'
        # )]

        logger.info("---------- Calling Coder ----------")
        state['current_agent'] = self.team.coder.member_name

        coder_result = self.team.coder.invoke({
            'project_name': state['project_name'],
            'project_folder_strucutre': state['project_folder_strucutre'],
            'requirements_document': state['requirements_document'].to_markdown(),
            'project_path': state['project_path'],
            'license_url': state['license_url'],
            'license_text': state['license_text'],
            'functions_skeleton': state['functions_skeleton'],
            'test_code': state['test_code'],
            'current_task': state['current_task'],
            'current_planned_task': state['current_planned_task'],
            'messages': state['messages']
        })

        state['current_planned_task'] = coder_result['current_planned_task']

        # TODO: on successfull case coder has to add updated fields to super state
        if state['current_planned_task'].task_status == Status.DONE:
            logger.info("Coder completed work package")

            state['agents_status'] = f'{self.team.coder.member_name} Completed'
        elif state['current_planned_task'].task_status == Status.ABANDONED:
            logger.info("Coder unable to complete the work package due to : %s",
                        state['current_planned_task'])

            state['agent_status'] = f"{self.team.coder.member_name} Completed With Abandonment"
        else:
            logger.info("Coder awaiting for additional information\nCoder Query: %s",
                        state['current_planned_task'])

            state['agents_status'] = f'{self.team.coder.member_name} Awaiting'

        self.called_agent = self.team.coder.member_id
        self.responses[self.team.coder.member_id].append(
            ("Returned from Coder", state['current_planned_task']))

        return state

    def call_test_code_generator(self, state: SupervisorState) -> SupervisorState:
        """
        """

        state['messages'] += [(
            ChatRoles.AI,
            'Calling Test Code Generator Agent'
        )]

        logger.info("---------- Calling Test Code Generator ----------")
        state['current_agent'] = self.team.tests_generator.member_name

        test_coder_result = self.team.tests_generator.invoke({
            'project_name': state['project_name'],
            'project_folder_strucutre': state['project_folder_strucutre'],
            'requirements_document': state['requirements_document'].to_markdown(),
            'project_path': state['project_path'],
            'license_url': state['license_url'],
            'license_text': state['license_text'],
            'current_task': state['current_task'],
            'current_planned_task': state['current_planned_task'],
            'messages': []
        })

        state['current_planned_task'] = test_coder_result['current_planned_task']

        if state['current_planned_task'].task_status == Status.INPROGRESS:

            # side effect of workaround added in TestGenerator.
            # Doing this for coder.
            state['current_planned_task'].task_status = Status.NEW

            logger.info("Test Code Generator completed work package")
            state['agents_status'] = f'{self.team.tests_generator.member_id} Completed'

            # I feel if these are part of PlannedTask, It makes more sense then to be in super state
            # because for every coding task these varies.
            state['test_code'] = test_coder_result['test_code']
            state['functions_skeleton'] = test_coder_result['functions_skeleton']

        elif state['current_planned_task'].task_status == Status.ABANDONED:
            logger.info("Test Coder Generator unable to complete the work package due to : %s",
                        state['current_planned_task'])
            state['agent_status'] = f'{self.team.tests_generator.member_id} Completed With Abandonment'
        else:
            logger.info("Test Coder Generator awaiting for additional information\nCoder Query: %s",
                        state['current_planned_task'])
            state['agents_status'] = f'{self.team.tests_generator.member_id} Generator Awaiting'

        self.called_agent = self.team.tests_generator.member_id
        self.responses[self.team.tests_generator.member_id].append(
            ("Returned from Test Coder Generator", state['current_planned_task']))

        return state

    def call_supervisor(self, state: SupervisorState) -> SupervisorState:
        """
        Manager of for the team. Makes decisions based on the current state of the project.
        """

        logger.info(f"{self.team.supervisor.member_name} has been called.")
        self.called_agent = self.team.supervisor.member_id
        # state['current_agent'] = self.team.supervisor.member_name
        if state['project_status'] == PStatus.RECEIVED:
            # When the project is in the 'RECEIVED' phase:
            # - RAG agent has to be called.
            # - Prepare additional information required by the team for further processing.

            state['messages'] += [
                (
                    ChatRoles.AI,
                    f"The Genpod team has started working on the project with ID: {state['project_id']} and the following microservice ID: {state['microservice_id']}."
                ),
                (
                    ChatRoles.AI,
                    "RAG agent can now gather necessary information to begin the project."
                ),
                (ChatRoles.AI, "When the project is in the 'RECEIVED' phase, the RAG agent is called to gather any additional information required by the team for further processing.")
            ]

            # create a task for rag agent
            state['current_task'] = Task(
                description='retrieve additional context from RAG system',
                task_status=Status.NEW,
                additional_info='',
                question=state['original_user_input']
            )
            state['project_status'] = PStatus.NEW

            logger.info(
                f"{self.team.supervisor.member_name}: Created task for RAG agent to gather additional info for the user requested project. Project Status moved to {state['project_status']}")

            return state
        elif state['project_status'] == PStatus.NEW:
            # When the project status is 'NEW':
            # - The RAG Agent task is complete.
            # - The next step is to involve the architect to generate the requirements document for the team.

            # If the task is marked as done, it means the RAG agent has gathered the additional information
            # needed for the team to begin the project.

            # state['messages'] += [
            #     (
            #         ChatRoles.AI,
            #         " When the project status is 'NEW',The RAG Agent task is complete. The next step is to involve the architect to generate the requirements document for the team. If the task is marked as done, it means the RAG agent has gathered the additional information needed for the team to begin the project."
            #     )

            # ]

            if state['current_task'].task_status == Status.DONE:
                if self.is_initial_additional_info_ready:
                    state['project_status'] = PStatus.INITIAL

                    # create a new task for the architect
                    state['current_task'] = Task(
                        description=self.prompts.architect_call_prompt.format(),
                        task_status=Status.NEW,
                        additional_info=state['rag_retrieval'],
                        question=''
                    )

                    state['messages'] += [
                        # (
                        #     ChatRoles.AI,
                        #     "RAG agent has gathered the additional information."
                        # ),

                        (
                            ChatRoles.AI,
                            " Once the project is initiated, the architect gathers requirements, and if additional information is needed, RAG is used to assist during this phase."
                        ),
                        # (

                        #     ChatRoles.AI,
                        #     " When the project is in the 'INITIAL' phase: 1. The architect has either completed their tasks or is waiting for additional information. If the architect has completed their tasks: Change the project status to 'EXECUTING' and proceed with the next steps. If the architect is still waiting for additional information: - Change the project status to 'MONITORING' and continue monitoring the situation."
                        # ),
                        (
                            ChatRoles.AI,
                            "A New task has been created for the Architect agent"
                        )
                    ]

                    logger.info(
                        f"{self.team.supervisor.member_name}: RAG agent has finished preparing additional information for team members.")
                    logger.info(
                        f"{self.team.supervisor.member_name}: Created new task for architect to work on requirements document. Moved Project to {state['project_status']} phase.")

            self.calling_agent = self.team.supervisor.member_id

            return state
        elif state['project_status'] == PStatus.INITIAL:
            # When the project is in the 'INITIAL' phase:
            # 1. The architect has either completed their tasks or is waiting for additional information.
            #
            # If the architect has completed their tasks:
            # - Change the project status to 'EXECUTING' and proceed with the next steps.
            #
            # If the architect is still waiting for additional information:
            # - Change the project status to 'MONITORING' and continue monitoring the situation.

            # Architect has prepared all the required information.
            if state['current_task'].task_status == Status.DONE:
                state['project_status'] = PStatus.EXECUTING

                state['messages'] += [
                    (

                        ChatRoles.AI,
                        "Architect agent has prepared the requirements document for the team."
                    ),
                    (

                        ChatRoles.AI,
                        "Now it should go to the supervisor agent to change the status."
                    ),
                    (
                        ChatRoles.AI,
                        " If the current task status is DONE and  the project status is EXECUTING, call back the SUPERVISOR AGENT to get new task status "
                    ),
                    # If tasks are already planned, the Coder and Tester will proceed with them. This process is triggered when the Architect finalizes the requirements, when the Coder and Tester complete their tasks, or when all planned tasks are finished, prompting the Planner to prepare new tasks.


                ]

                logger.info(
                    f"{self.team.supervisor.member_name}: Architect agent has prepared the requirements document for the team.")
                logger.info(
                    f"{self.team.supervisor.member_name}: Planner can take initiative and prepare the tasks for the team. Moved Project to {state['project_status']} phase.")
            elif state['current_task'].task_status == Status.AWAITING:
                # Architect need additional information to complete the assigned task. architect provides query in the task packet
                # use it to query RAG.
                self.previous_project_status = state['project_status']
                state['project_status'] = PStatus.MONITORING

                state['messages'] += [
                    (
                        ChatRoles.AI,
                        "Call RAG agent now to gather additional information."
                    ),
                    # (
                    #     ChatRoles.AI,
                    #     " When the project status is 'MONITORING, the current agent is awaiting and needs help of other agent to work"
                    # )
                ]

                logger.info(
                    f"{self.team.supervisor.member_name}: Architect agent has requested the additional information.")
                logger.info(
                    f"{self.team.supervisor.member_name}: RAG Agent will respond to the query. Moved Project to {state['project_status']} phase.")
            # else:
            #     state['messages'] += [
            #         (ChatRoles.AI, f"Current agent {state['current_agent']} doesn't have enough information to proceed. Consider calling other agents.")]

            return state
        elif state['project_status'] == PStatus.MONITORING:
            # When the project status is 'MONITORING':
            # - If the current task status is 'RESPONDED':
            #   - Change the project status back to the previous state and proceed with the next steps.

            if state['current_task'].task_status == Status.RESPONDED:
                state['project_status'] = self.previous_project_status
                self.calling_agent = self.called_agent

                state['messages'] += [
                    (
                        ChatRoles.AI,
                        "Team has responded to the query from team member."
                    ),

                    (
                        ChatRoles.AI,
                        "Query has been answered. Moved Project to {state['project_status']} phase."
                    )
                ]

                logger.info(
                    f"Query has been answered. Moved Project to {state['project_status']} phase.")

            return state
        elif state['project_status'] == PStatus.EXECUTING:
            # When the project status is 'EXECUTING':
            # - The Planner, Coder, and Tester should work on the tasks that have been prepared by the architect.
            #
            # If there are no planned tasks:
            # - The Planner needs to prepare new tasks.
            #
            # If there are planned tasks:
            # - The Coder and Tester should work on these tasks.

            # Three scenario ofr this block of code to get triggered
            # Architect agent has finished generating the requirements documents and tasks
            # or
            # Coder and Tester completed their task.
            # or
            # all planned tasks were done.
            # Call Planner to prepare planned tasks.

            # state['messages'] += [
            #     (
            #         ChatRoles.AI,
            #         "Project is in EXECUTING status. "
            #     ),

            #     (
            #         ChatRoles.AI,
            #         "Planner can take initiative and prepare the tasks for the team."
            #     ),

            # (
            #     ChatRoles.AI,
            #     """ If are_planned_tasks_in_progress {are_planned_tasks_in_progress} is False
            #                 Action: The Planner should be called to prepare and break down the tasks.
            #                 Agent: call_planner."""
            # ),
            # ]

            try:
                state['tasks'].update_task(state['current_task'])
                # state['messages'] += [

                #     (
                #         ChatRoles.AI,
                #         " If no tasks are available, the Planner is responsible for creating new ones."

                #     ),
                #     (
                #         ChatRoles.AI,
                #         "If planned tasks are in progress, Coder and Tester will complete them."
                #     ),
                #     (
                #         ChatRoles.AI,
                #         "If function generation is required and test code has not been generated, Test Code Generator will be called."
                #     ),
                #     (
                #         ChatRoles.AI,
                #         "If test code is already generated, proceed to code generation with the Coder."
                #     ),
                #     (
                #         ChatRoles.AI,
                #         "If the task is done or abandoned, Supervisor will assign new tasks for the Planner."
                #     )
                # ]

            except Exception as e:
                logger.error(
                    f"`state['tasks']` received an task which is not in the list. \nException: {e}")

            # If any task is abandoned just move on to new task for now. Already task status is updated in the task list.
            # Will decide on what to do with abandoned tasks later.
            if state['current_task'].task_status == Status.DONE or state['current_task'].task_status == Status.ABANDONED:
                next_task = state['tasks'].get_next_task()

                state['messages'] += [
                    (
                        ChatRoles.AI,
                        " Supervisor will assign new tasks for the Planner."
                    )
                ]

                # All task must have been finished.
                if next_task is None:
                    # TODO: Need to consider the Abandoned Tasks. Before considering the task as complete.
                    state['project_status'] = PStatus.DONE
                else:
                    state['current_task'] = next_task

                    requirements_doc = state['requirements_document'].to_markdown(
                    )
                    # TODO - LOW: Better to take away this there is redundancy of storing requirements document
                    # In Super State and Task as task will persisted in DB.
                    state['current_task'].additional_info = requirements_doc + \
                        '\n' + state['rag_retrieval']
                    # state['messages'] += [
                    #     (
                    #         ChatRoles.AI,
                    #         "Task is DONE or ABANDONED, moving to the next task."
                    #     ),
                    # (
                    #     ChatRoles.AI,
                    #     f"Next task is: {state['current_task'].description}"
                    # )
                    # ]
            elif state['current_task'].task_status == Status.AWAITING:
                # Planner needs additional information
                # Architect was responsible for answering the query if not then rag comes into play.
                state['messages'] += [

                    (
                        ChatRoles.AI,
                        "Planner needs additional information from the team."
                    ),
                    (
                        ChatRoles.AI,
                        "Ask Architect agent additional information."
                    ),
                    (
                        ChatRoles.AI,
                        "If Architect agent has not provided any additional information, direct it to RAG agent for help."
                    ),
                ]
                self.previous_project_status = state['project_status']
                state['project_status'] = PStatus.MONITORING
                self.calling_agent = self.called_agent
            elif state['current_task'].task_status == Status.INPROGRESS:
                # update the planned _task status in the list
                try:
                    state['planned_tasks'].update_task(
                        state['current_planned_task'])
                except Exception as e:
                    logger.error(
                        f"`state['planned_tasks']` received an task which is not in the list. \nException: {e}")

                if state['current_planned_task'].task_status == Status.NONE or state['current_planned_task'].task_status == Status.DONE or state['current_planned_task'].task_status == Status.ABANDONED:
                    next_planned_task = state['planned_tasks'].get_next_task()

                    if next_planned_task is None:
                        self.are_planned_tasks_in_progress = False

                        state['current_task'].task_status = Status.DONE
                        state['messages'] += [
                            (
                                ChatRoles.AI,
                                " Marking current task as DONE."
                            )
                        ]
                    else:
                        state['current_planned_task'] = next_planned_task
                        self.are_planned_tasks_in_progress = True
                        # state['messages'] += [

                        # (
                        #     ChatRoles.AI,
                        #     """ If are_planned_tasks_in_progress is False
                        #     Action: The Planner should be called to prepare and break down the tasks.
                        #     Agent: call_planner."""
                        # ),
                        # (
                        #     ChatRoles.AI,
                        #     "Moving to the next planned task."
                        # ),
                        # (
                        #     ChatRoles.AI,
                        #     f"Next planned task: {state['current_planned_task'].description}"
                        # ),
                        # (
                        #     ChatRoles.AI,
                        #     "Checking if function generation is required for the next planned task."
                        # ),
                        # (
                        #     ChatRoles.AI,
                        #     "If function generation is required and test code is not yet generated, call the Test Code Generator."
                        # ),
                        # (
                        #     ChatRoles.AI,
                        #     "If test code is already generated, proceed to check if code generation is required."
                        # ),
                        # (
                        #     ChatRoles.AI,
                        #     "If code generation is required, Coder will be called to complete the task."
                        # ),
                        # ]
                        self.calling_agent = self.team.supervisor.member_id

            return state
        elif state['project_status'] == PStatus.HALTED:
            # When the project status is 'HALTED':
            # - The application requires human intervention to resolve issues and complete the task.

            # TODO: Figure out when this stage occurs and handle the logic
            state['messages'] += [
                (
                    ChatRoles.AI,
                    "Project status is HALTED. Human intervention is required to resolve issues."
                )
            ]
            return state
        elif state['project_status'] == PStatus.DONE:
            # When the project status is 'DONE':
            # - All tasks have been completed.
            # - The requested output for the user is ready.

            # TODO: Figure out when this stage occurs and handle the logic
            state['messages'] += [
                (
                    ChatRoles.AI,
                    "Project status is DONE. All tasks have been completed."
                )
            ]
            return state
        else:
            return state

    def call_planner(self, state: SupervisorState) -> SupervisorState:
        """
        """

        logger.info("----------Calling Planner----------")

        planner_result = self.team.planner.invoke({
            'current_task': state['current_task'],
            'project_path': state['project_path']
        })

        # TODO - LOW: Perfromance, Memory, Code Enhancement
        # Currenlty planner is returning list of task thorugh `response`
        # key of the state and also returning `planned_tasks` and `planned_tasks_map`
        # There is a redundancy in this way of storing the info.
        # Other issue is `current_task` being receive from planner now is completely
        # different, you can see the below line, this means we are losing the track the
        # task assigned to planner. At this stage `current_task` should always be the previously
        # assigned task. FYI `current_task` is expected to hold tasks from `tasks` list and `planned_tasks`
        # list. so `current_task` field task might be used to update the status of task in those fields.
        # if task is not present in the list then it raises an EXCEPTION.

        # TODO - LOW: Performance, Memory Enhancement
        # Currenlty `additional_info` field of Task object is being used to send
        # some information like `requirements_document`. This is saving same information
        # at two points as tasks are being persisted. Better way to do this, give information on
        # demand/required meaning `requirements_document` is only needed by planner when an task
        # has to be broken down to small task, this will be triggered by graph invocation.
        # send the information as the field of the graph should work.
        state['current_task'] = planner_result['response'][-1]

        if state['current_task'].task_status == Status.DONE:
            logger.info("----------Response from Planner Agent----------")
            logger.info("Planner Response: %r",
                        planner_result['planned_task_map'])

            state['agents_status'] = f'{self.team.planner.member_name} completed'
            self.called_agent = self.team.planner.member_id
            self.responses[self.team.planner.member_id].append(
                ("Returned from Planner", state['current_task']))
        elif state['current_task'].task_status == Status.INPROGRESS:
            # TODO - LOW: Move this logic to planner
            # Its better if planner only returning planned_tasks as output.
            # `planned_task_map` `planned_task_requiremtns` is an redundancy.
            state['planned_task_map'] = {**planner_result['planned_task_map']}
            state['planned_task_requirements'] = {
                **planner_result['planned_task_requirements']}

            # TODO: use the response packet and build the planned tasks list
            # Get the workpackages created by planner for the current task a.k.a. deliverable

            for wpn, is_function_generation_required in state['planned_task_map'][state['current_task'].description].items():
                # for each workpackage we need to create a planned_task

                state['planned_tasks'].add_task(
                    PlannedTask(
                        description=json.dumps(
                            {
                                "work_package_name": wpn,
                                **state['planned_task_requirements'][wpn],
                            }
                        ),
                        task_status=Status.NEW,
                        is_function_generation_required=is_function_generation_required
                    )
                )

                # state['messages'] += [

                #     (
                #         ChatRoles.AI,
                #         f"""
                #         If is_function_generation_required {state['current_planned_task'].is_function_generation_required} is True:
                #             Check if is_test_code_generated {state['current_planned_task'].is_test_code_generated} is False - If false then
                #                 Action: The Tester must complete the test code generation before proceeding further.
                #                 Agent: call_test_code_generator.
                #             If is_test_code_generated {state['current_planned_task'].is_test_code_generated} is True:
                #                 Action: Proceed to the next step.
                #         """
                #     ),

                #     (
                #         ChatRoles.AI,
                #         f"""
                #         If {state['current_planned_task'].is_code_generate} is False and PlannedTask {state['planned_tasks'].task_status} is NEW :
                #             Action: The Coder can complete the task independently.
                #             Agent: call_coder.

                #         """
                #     ),
                # ]

            state['agent_status'] = f"{self.team.planner.member_name} built the work packages"
            self.called_agent = self.team.planner.member_id
            self.responses[self.team.planner.member_id].append(
                ("Returned from Planner", state['current_task']))

            logger.info("----------Response from Planner Agent----------")
            logger.info("Planner Response: %r",
                        planner_result['planned_task_map'])

            return {**state}
        else:
            logger.info("----------Response from Planner Agent----------")
            logger.info("Planner Response: %s", state['current_task'].question)

            state['agents_status'] = f'{self.team.planner.member_name} Awaiting'
            self.called_agent = self.team.planner.member_id
            self.responses[self.team.planner.member_id].append(
                ("Returned from Planner with a question", state['current_task'].question))

        return state

    def call_human(self, state: SupervisorState) -> SupervisorState:
        # Display relevant information to the human
        # pprint(f"----------Supervisor current state----------\n{state}")
        # Prompt for input
        if state['current_task'].question != '':
            # Display the current task being performed to the user
            logger.info(
                "----------Current Task that needs your assistance to proceed----------")
            logger.info("Current Task: %r", state['current_task'])
            # Get human input
            human_input = input(
                f"Please provide additional input for the question:\n{state['current_task'].question}")

            # Append the human input to current_task additional_info
            state['current_task'].additional_info += '\nHuman_Response:\n' + human_input

            # Update the project status back to executing
            state['project_status'] = PStatus.EXECUTING

            # Add the human responses to the rag cache for future queries and maintain a copy in state too
            human_feedback = (state['current_task'].question,
                              f'Response from Human: {human_input}')
            state['human_feedback'] += [human_feedback]
            self.rag_cache.add(state['current_task'].question, human_input)

        else:
            logger.info(
                "----------Unable to handle Human Feedback currently so ending execution----------")

        human_input = input(
            f"Please provide additional input for the question:\n{state['current_task'].question}")

        # Process the input and update the state
        state['human_feedback'] += [human_input]
        state['project_status'] = PStatus.EXECUTING
        # state.human_feedback = human_input

        return state

    def save_execution_time(self, state: SupervisorState, task_id, start_time, end_time, duration, agent_name):

        # Save the metrics to the database
        DATABASE_PATH = get_client_local_db_file_path()
        db = Database(DATABASE_PATH)

        metrics = db.metrics_table.insert(
            state['project_id'], state['microservice_id'], task_id, start_time, end_time, duration, agent_name)

        return metrics

    def delegator(self, state: SupervisorState) -> str:
        """
        Delegates the tasks across the agents based on the current project status

        Parameters:
        state (SupervisorState): The current state of the project.

        Returns:
        str: The next action to be taken based on the project status.
        """

        # if state['project_status'] == PStatus.NEW:
        #     # Project has been received by the team.
        #     # RAG(team member) now need to gather additonal information for the project
        #     # additional information? yep a more detailed information about the project.
        #     # user input would be to vague to start working on the project and results in a
        #     # more generic output. so we need to more specific on what user is expecting.
        #     # RAG holds the some standards documents and it fetches the relevant information related
        #     # to the project to help team members efficient and qualified output.

        #     logger.info(
        #         f"Delegator: Invoking call_rag due to Project Status: {PStatus.NEW}")
        #     return 'call_rag'

        if state['project_status'].value != PStatus.HALTED.value:
            # if state['current_task'].task_status == Status.DONE and state['project_status'] == PStatus.EXECUTING:
            #     'call_supervisor'
            classifier_output = self.classifier.classify(state)
            if classifier_output.selected_agent == None:
                reason = classifier_output.reason
                state['messages'] += [
                    (ChatRoles.AI, reason)
                ]
                return 'call_supervisor'
            state['are_planned_tasks_in_progress'] = self.are_planned_tasks_in_progress
            state['visited_agents'].append(
                classifier_output.selected_agent.member_name)

            state['current_agent'] = classifier_output.selected_agent.member_name

            return f'call_{classifier_output.selected_agent.alias}'
        else:
            return "update_state"

        # elif state['project_status'] == PStatus.INITIAL:
        #     # Once the project is ready with additional information needed. Team can starting working on the project
        #     # architect is first team member who receives the project details and prepares the the requirements out of it.
        #     # In this process if architect need aditional information thats when RAG comes into play at this phase of Project.
        #     if self.is_initial_additional_info_ready:
        #         logger.info(
        #             f"Delegator: Invoking call_architect due to Project Status: {PStatus.INITIAL}")
        #         return 'call_architect'
        # elif state['project_status'] == PStatus.MONITORING:
        #     # During query answering phase by agents PROJECT_STATUS will be in this phase

        #     # RAG is the source for the information. It can fetch relevant information from vector DB for the given query.
        #     if state['current_task'].task_status == Status.AWAITING:
        #         logger.info(
        #             f"Delegator: Invoking call_rag due to Project Status: {PStatus.MONITORING} and Task Status: {Status.AWAITING}.")
        #         return 'call_rag'
        # elif state['project_status'] == PStatus.EXECUTING:
        #     # During the execution phase, there are two key scenarios:
        #     # 1. The planner breaks down complex tasks into smaller, manageable planned tasks.
        #     # 2. Coder or tester completes the planned tasks.
        #     #
        #     # The `are_planned_tasks_in_progress` flag indicates whether there are any tasks in the planned tasks list.
        #     # If this flag is True, it means that planned tasks are the current priority.
        #     # If the list is empty, it signifies that there are no planned tasks, and any remaining tasks should be further broken down by the planner.
        #     if self.are_planned_tasks_in_progress:
        #         if state['current_planned_task'].is_function_generation_required:
        #             if not state['current_planned_task'].is_test_code_generated:
        #                 logger.info(
        #                     f"Delegator: Invoking call_test_code_generator due to Project Status: {PStatus.EXECUTING} and PlannedTask involving is_function_generation_required and is_test_code_generated.")
        #                 return 'call_test_code_generator'

        #         # Other conditions like is_code_generated from PlannedTask object is also useful
        #         # to figure out if coder has already completed the task.
        #         if not state['current_planned_task'].is_code_generate:
        #             logger.info(
        #                 f"Delegator: Invoking call_code due to Project Status: {PStatus.EXECUTING} and PlannedTask Status: {Status.NEW}.")
        #             return 'call_coder'
        #     else:
        #         if state['current_task'].task_status == Status.NEW:
        #             logger.info(
        #                 f"Delegator: Invoking call_planner due to Project Status: {PStatus.EXECUTING} and Task Status: {Status.NEW}.")
        #             return 'call_planner'

        #     # occurs when architect just completed the assigned task(generating documents and tasks)
        #     # and now supervisor has to assign tasks for planner.
        #     logger.info(
        #         f"Delegator: Invoking call_supervisor due to Project Status: {PStatus.EXECUTING}.")
        #     return 'call_supervisor'
        # elif state['project_status'] == PStatus.HALTED:
        #     # There may be situations where the LLM (Language Learning Model) cannot make a decision
        #     # or where human input is required to proceed. This could be due to ambiguity or intentional
        #     # scenarios that need human judgment to ensure progress.

        #     logger.info(
        #         f"Delegator: Invoking call_human due to Project Status: {PStatus.HALTED}.")
        #     return 'update_state'  # 'Human'

        # logger.info(f"Delegator: Invoking update_state.")
        # return "update_state"
