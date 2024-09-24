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
    # PROJECT_INPUT = refined_prompt.invoke(PROJECT_INPUT)

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

    print(f"Project generated successfully! Project ID: {result['project_id']}, Project Name: {result['project_name']}, Location: {PROJECT_PATH}.")
    logger.info(f"Project generated successfully! Project ID: {result['project_id']}, Project Name: {result['project_name']}, Location: {PROJECT_PATH}.")