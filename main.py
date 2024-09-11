"""
Driving code file for this project.
"""
import os

from agents.supervisor.supervisor_state import SupervisorState
from configs.database import get_client_local_db_file_path
from configs.project_config import ProjectConfig
from configs.project_path import set_project_path
from database.database import Database
from genpod.team import TeamMembers
from utils.logs.logging_utils import logger
from utils.time import get_timestamp

print("\n\nWe greatly appreciate your interest! Please note that we are in the midst of active development and are striving to make improvements every day!\n\n")

if __name__ == "__main__":
    TIME_STAMP = get_timestamp()
    logger.info(f"Project Generation has been triggered at {TIME_STAMP}!")

    # Initialize the project config
    config = ProjectConfig()
    logger.info("Project configuration loaded!")

    USER_ID = int(os.getenv("USER_ID"))
    if USER_ID is None:
        raise EnvironmentError(
            "The `USER_ID` environment variable is not set. Please add it to the '.env' file with the format: USER_ID=4832")

    DATABASE_PATH = get_client_local_db_file_path()
    db = Database(DATABASE_PATH)

    # setup database
    # Tables are created only if they doesn't exist
    db.setup_db()

    PROJECT_INPUT = """
    Project Overview:
    I want to develop a Title Requests Micro-service adhering to MISMO v3.6 standards to handle get_title service using GET REST API Call in .NET
    Utilize a MongoDB database (using the provided connection details: \"mongodb://localhost:27017/titlerequest\").
    Host the application at "https://crbe.com".
    """

    LICENSE_URL = "https://raw.githubusercontent.com/intelops/tarian-detector/8a4ff75fe31c4ffcef2db077e67a36a067f1437b/LICENSE"
    LICENSE_TEXT = "SPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of CRBE & the Organization created CRBE"

    PROJECT_PATH = set_project_path(timestamp=TIME_STAMP)
    logger.info(f"Project is being saved at location: {PROJECT_PATH}")

    # Database insertion - START
    # insert the record for the project being generated in database
    project_details = db.projects_table.insert(
        "", PROJECT_INPUT, "", PROJECT_PATH, USER_ID, LICENSE_TEXT, LICENSE_URL)
    logger.info(
        f"Records for new project has been created in the database with id: {project_details['id']}")

    microservice_details = db.microservices_table.insert(
        "", project_details['id'], "", USER_ID)
    logger.info(
        f"Records for new microservice has been created in the database with id: {microservice_details['id']}")

    sessions_details = []
    for key, agent in config.agents_config.items():
        session_detail = db.sessions_table.insert(
            project_details['id'], microservice_details['id'], USER_ID)
        sessions_details.append(session_detail)

        agent.set_thread_id(session_detail['id'])

    # logger.info(
    #     f"Records for new session has been created in the database with ids: {", ".join(f"{value.agent_id}: {value.thread_id}" for key, value in config.agents_config.items())}")
    # Database insertion - END

    genpod_team = TeamMembers(DATABASE_PATH, config.collection_name)
    genpod_team.supervisor.set_recursion_limit(500)
    genpod_team.supervisor.graph.agent.setup_team(genpod_team)

    supervisor_response = genpod_team.supervisor.stream({
        'project_id': project_details['id'],
        'microservice_id': microservice_details['id'],
        'original_user_input': PROJECT_INPUT,
        'project_path': PROJECT_PATH,
        'license_url': LICENSE_URL,
        'license_text': LICENSE_TEXT,
    })
    logger.info(
        f"The Genpod team has been notified about the new project. {genpod_team.supervisor.member_name} will begin work on it shortly.")

    result: SupervisorState = None
    for res in supervisor_response:
        for node_name, super_state in res.items():
            logger.info(
                f"Received state update from supervisor node: {node_name}. Response details: {super_state}")
            result = super_state

    # TODO: DB update should happen at for every iteration in the above for loop
    # write a logic to identify changes in the state.
    # NOTE: db doesnt store all the value from the state, it only stores few fields
    # from the state. so, logic should identify the changes to the fields that db stores
    # If there is a change in state then only update the db.
    db.projects_table.update(
        result['project_id'],
        project_name=result['project_name'],
        status=str(result['project_status']),
        updated_by=USER_ID
    )
    db.microservices_table.update(
        result['microservice_id'],
        microservice_name=result['project_name'],
        status=str(result['project_status']),
        updated_by=USER_ID
    )


# User input {user_prompt}
#         You are AgentMatcher, an intelligent assistant designed to analyze the project flow, project status, task status and flags to select the most suitable agent.
#         Your task is to understand the project flow, the input boolean flags and determine which agent would be best equipped at any given point based on the status provides and flow of interactions.

#         You can choose from one of the following agents: <agents> {agent_descriptions} </agents>
#         If you are unable to select an agent, Select the Supervisor agent.

#         The project flow is as follows:
#         Project Flow: {project_flow}
#         The available flags are as follows: <flags> {flags} </flags>
#         task status: {current_status}
#         Project status: {project_status}


#         Check the project status and refer to the message history to determine the course of action.
#         Conversation History: {history}

#         Guidelines for classification:
#         Agent Type: Choose the most appropriate agent type based on the nature of the query.
#         For follow-up responses, use the same agent type as the previous interaction.
#         Priority: Follow the instructions.
#             High: The available flags are as follows: <flags> {flags} </flags>


#         For follow-ups, relate the intent to the ongoing conversation.
#         Confidence: Indicate how confident you are in the classification.
#             High: Clear, straightforward requests or clear follow-ups
#             Medium: Requests with some ambiguity but likely classification
#             Low: Vague or multi-faceted requests that could fit multiple categories
#         Is Followup: Indicate whether the input is a follow-up to a previous interaction.
#         Reason: Provide a brief explanation of why a particular agent was selected based on the project flow and other indicators like the project status, task status and current agent.

#         You can track the visited agents here:
#         <visited_agents>
#         {visited_agents}
#         </visited_agents>


#         Examples:

#         Selected Agent: Architect agent
#         Confidence: 0.95
#         Reason: The calling agent is RAG, so you have all the required information to proceed to the architectural agent. Also the project status is INITIAL and Task status is  NEW.

#         Selected Agent: RAG agent
#         Confidence: 0.95
#         Reason: The calling agent is Architect agent, so you have need more information to proceed. Also the project status is INITIAL and Task status is  AWAITING.

#         Selected Agent: Supervisor agent
#         Confidence: 0.95
#         Reason: The calling agent is Architect agent. Also the project status is EXECUTING and Task status is DONE.


#         Selected Agent: Planner agent
#         Confidence: 0.95
#         Reason: The calling agent is Supervisor agent. Also the project status is EXECUTING and Task status is NEW. The flag are_planned_task_in_progress is False

#         Selected Agent: Tester agent
#         Confidence: 0.95
#         Reason: The flag are_planned_task_in_progress is True, is_function_generation_required is True. is_test_code_generated is False

#         Selected Agent: Coder agent
#         Confidence: 0.95
#         Reason: The project status is EXECUTING. The flag are_planned_task_in_progress is True, is_code_generate is False.


#         Skip any preamble and provide only the response in the specified format.

#                         """,
#         input_variables=["agent_descriptions", "history",
#                          "current_agent", "current_status", "user_prompt", "visited_agents", "project_status", "project_flow", "flags"],
#     )

    #     template="""
    #     User input {user_prompt}
    #             You are AgentMatcher, an intelligent assistant designed to analyze the project flow and select the most suitable agent.
    #             Your task is to understand the project flow, and determine which agent would be best equipped at any given point based on the status provides and flow of interactions.

    #             You can choose from one of the following agents: <agents> {agent_descriptions} </agents>

    #             If you are unable to select an agent, escalate the query to the Supervisor agent.

    #             High Priority:
    #             When selecting the next agent, give the project flow high priority to maintain consistency and follow-up context. Always check for relevant history before selecting a new agent.

    #         Guidelines for Classification:
    #             Project Flow: {project_flow}
    #             Project Flow: Understand the project flow to know the step by step process.
    #             Agent Type: Choose the most appropriate agent type based on the project flow, ensuring consistency with past interactions where applicable.
    #             High Priority: Look at the data here serialized output below and extract boolean flag information from it
    #             to select the next agent.
    #            {flags}

    #             Current Agent and Status:

    #             Consider the current agent details and status before deciding the next course of action.
    #             Check the project status and refer to the message history to determine the course of action.
    #             Calling Agent: {current_agent}
    #             task status: {current_status}
    #             Project status: {project_status}

    #             Conversation History: {history}
    #             Confidence: Indicate how confident you are in the classification.

    #             High: Clear, straightforward requests or follow-ups
    #             Medium: Requests with some ambiguity but likely classification
    #             Low: Vague or multi-faceted messages that could fit multiple categories
    #             Reason: Provide a brief explanation of why a particular agent was selected based on the project flow and other indicators like the project status, task status and current agent.

    #             You can track the visited agents here:
    #             <visited_agents>
    #             {visited_agents}
    #             </visited_agents>

    #             Examples:
    #             Initial query without prior context in the message history:

    #             Message History: "What’s the architectural framework for this project?"
    #             Selected Agent: Architect agent
    #             Confidence: 0.95
    #             Reason: The message directly relates to project architecture, which is the Architect agent's domain.
    #             Switching from code-related to planning-related:

    #             Message History:
    #             "[Coder]: There’s a typo in your function; fix it to proceed."
    #             "[Message]: What’s the next set of tasks for the project?"
    #             Selected Agent: Project Planner agent
    #             Confidence: 0.9
    #             Reason: The query is now focused on planning the next set of tasks, which falls under the Project Planner agent's role.
    #             Follow-up query for the same agent:

    #             Message History:
    #             "[Architect]: The architecture will follow a microservices-based approach."
    #             "[Message]: Can you give me more details on how the components will communicate?"
    #             Selected Agent: Architect agent
    #             Confidence: 0.95
    #             Reason: The user is asking for further clarification on architecture, which continues the conversation with the Architect agent.
    #             Human intervention needed due to errors:

    #             Message History:
    #             "[Knowledge Graph Generator]: I’ve generated the graph schema."
    #             "[Message]: The graph keeps failing when I run the data through it."
    #             Selected Agent: Human Intervention Specialist
    #             Confidence: 0.85
    #             Reason: Automated systems are encountering issues, and the Human Intervention Specialist is best equipped to handle such problems.
    #             Code Review request:

    #             Message History:
    #             "[Coder]: Code implementation is complete."
    #             "[Message]: Can someone review the code for adherence to clean code standards?"
    #             Selected Agent: Code Reviewer
    #             Confidence: 0.9
    #             Reason: The request specifically pertains to code review, which is the responsibility of the Code Reviewer agent.

    #                         Skip any preamble and provide only the response in the specified format.

    #                     """,
    #     input_variables=["agent_descriptions", "history",
    #                      "current_agent", "current_status", "user_prompt", "visited_agents", "project_status", "project_flow", "flags"],
    # )
