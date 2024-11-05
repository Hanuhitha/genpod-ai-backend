"""
Driving code file for this project.
"""
import os
from neo4j import GraphDatabase

import requests
from agents.prompt_agent.prompt_agent import PromptAgent

from agents.supervisor.supervisor_state import SupervisorState
from agents.prompt_agent.prompt_graph import PromptGraph
from configs.database import get_client_local_db_file_path
from configs.project_config import ProjectConfig
from configs.project_path import set_project_path
from database.database import Database
from genpod.team import TeamMembers
from utils.logs.logging_utils import logger
from pydantic_models.constants import ChatRoles
from utils.time import get_timestamp
import asyncio
import websockets
from websockets.asyncio.server import serve
from rich.console import Console

from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
console = Console()

print("\n\nWe greatly appreciate your interest! Please note that we are in the midst of active development and are striving to make improvements every day!\n\n")


async def handle_connection(websocket):

    # logger.info("path", path)

    prompt_config = config.agents_config[config.agents.prompt.agent_id]
    prompt_engineer_graph = PromptGraph(
        prompt_config.llm, websocket, is_async=True, project_config=config)

    # if path:

    # Wait for the project input and request ID from CLI via WebSocket
    project_data = await websocket.recv()
    project_data = eval(project_data)
    project_input = project_data["user_input_prompt_message"]
    request_id = project_data["request_id"]

    logger.info(
        f"Received project input: {project_input} with request ID: {request_id}")

    # Configure the graph for the prompt agent
    graph_config = {
        "configurable": {
            "thread_id": prompt_config.thread_id,
        },
        'recursion_limit': 500,

    }

    response = {
        'original_user_input': project_input,
        'messages': [],
        'status': False,
        'request_id': request_id,
    }

    prompt_response = prompt_engineer_graph.app.astream(
        response,
        graph_config,
        stream_mode="values"
    )

    async for response in prompt_response:
        if not response['status']:
            # Send refined response to CLI via WebSocket
            logger.info(f'{response}')
        else:
            break


async def main():

    async with serve(handle_connection, "localhost", 8001, ping_interval=20, ping_timeout=None):
        print("WebSocket server started at ws://localhost:8001")
        await asyncio.Future()


def test_neo4j_connection():
    config = ProjectConfig()
    try:
        with config.neo4j_driver.session("neo4j") as session:
            # Run a simple test query to verify the connection
            result = session.run("RETURN 'Connection successful!' AS message")
            print(result.single()["message"])
    except Exception as e:
        print("Error connecting to Neo4j:", e)
    finally:
        config.close_neo4j_driver()


def connect():
    """Establish connection with Neo4j."""
    graphdb = GraphDatabase.driver(database="neo4j", uri="bolt://127.0.0.1:7689",
                                   auth=("neo4j", "password"))
    print(f"Connected to Neo4j")


if __name__ == "__main__":

    TIME_STAMP = get_timestamp()
    logger.info(f"Project Generation has been triggered at {TIME_STAMP}!")

    # graph = Neo4jGraph(url="bolt://localhost:7689", database="neo4j",
    #                    username="neo4j", password="password")

    # result = graph.query("RETURN 'Neo4j connected successfully!' AS message")
    # print(result)

    #                                )
    # session = graphdb.session()

    # q1 = "MATCH (x) return (x)"
    # session.run(q1)

    # Initialize the project config
    config = ProjectConfig()
    connect()
    test_neo4j_connection()

    logger.info("Project configuration loaded!")

    USER_ID = int(os.getenv("USER_ID"))
    if USER_ID is None:
        raise EnvironmentError(
            "The `USER_ID` environment variable is not set. Please add it to the '.env' file with the format: USER_ID=4832")

    DATABASE_PATH = get_client_local_db_file_path()
    db = Database(DATABASE_PATH)

    db.setup_db()

    PROJECT_INPUT = """
    Project Overview:
    I want to develop a Title Requests Micro-service adhering to MISMO v3.6 standards to handle get_title service using GET REST API Call in .NET
    Utilize a MongoDB database (using the provided connection details: \"mongodb://localhost:27017/titlerequest\").
    Host the application at "https://crbe.com".
    """
    sessions_details = []
    for key, agent in config.agents_config.items():
        session_detail = db.sessions_table.insert(
            '', '', USER_ID)
        sessions_details.append(session_detail)

        agent.set_thread_id(session_detail['id'])

    asyncio.run(main())
    # asyncio.get_event_loop().run_forever()

    # Run the async WebSocket handling

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

    print(
        f"Project generated successfully! Project ID: {result['project_id']}, Project Name: {result['project_name']}, Location: {PROJECT_PATH}.")
    logger.info(
        f"Project generated successfully! Project ID: {result['project_id']}, Project Name: {result['project_name']}, Location: {PROJECT_PATH}.")
