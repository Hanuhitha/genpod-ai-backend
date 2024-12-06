# cli/cli.py

import typer
import requests
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import time
import websockets
from websockets.asyncio.client import connect

from websockets.exceptions import ConnectionClosedOK
import uuid
import asyncio
# from utils.task_utils import generate_new_id fix this

from consts import API_URL, WS_URL, ping_timeout, close_timeout, WS_URLL

app = typer.Typer()
console = Console()


def generate_new_id(prefix: str = "") -> str:
    timestamp = str(int(time.time()))
    unique_id = uuid.uuid4()

    return f"{prefix}{timestamp}{unique_id.hex}"


@app.command()
def start_conversation():
    """
    Start the WebSocket conversation with the LLM agent via WebSockets.
    """
    request_id = generate_new_id()
    user_input_prompt_message = Prompt.ask(
        f"User Input Prompt Message")

    asyncio.run(websocket_conversation(request_id, user_input_prompt_message))


async def connect_websocket(WS_URL, request_id):
    print('connecting')
    websocket = await connect(f"{WS_URL}/{request_id}", ping_interval=20, ping_timeout=None)
    print('connected')
    return websocket


async def websocket_conversation(request_id: str, user_input_prompt_message: str):
    """
    WebSocket connection to submit project info and handle conversation with the server.
    """
    continue_connection = False

    try:
        websocket = await connect_websocket(WS_URL, request_id)
        console.print(
            f"[yellow]Connected to WebSocket for Request ID: {request_id}[/yellow]")

        # Step 1: Send the initial project info to the WebSocket server
        project_payload = {
            "request_id": request_id,
            "user_input_prompt_message": user_input_prompt_message
        }
        post_response = requests.post(
            f"{API_URL}/project_info", json=project_payload)
        if post_response.status_code == 200:
            console.print(
                f"[green]Project information submitted successfully![/green]")
        else:
            console.print(
                f"[red]Failed to submit project info: {post_response.text}[/red]")
            return
        await websocket.send(str(project_payload))
        console.print(
            f"[blue]Sent project input: {user_input_prompt_message}[/blue]")

        # Step 2: Wait for the server's response (via FastAPI and the Prompt Agent)
        while True:
            # await websocket.send("ping")  # Send a keep-alive ping
            # await asyncio.sleep(5)  # Adjust interval as needed

            # try:
            response = await websocket.recv()
            print(response)
            response = eval(response)

            if 'enhanced_prompt' in response:
                console.print(
                    f"[green]Server Response: {response['enhanced_prompt']}[/green]")
            if 'decision' in response:
                if response['decision'] == 'YES':
                    await websocket.close()
                    break

            if 'response' in response:
                console.print(
                    f"[red]Server Response: {response['response']}[/red]")
            # Ask if the user wants to provide additional input
            additional_input = Prompt.ask(
                "Provide additional input (or type 'yes' to stop)")

            # Send additional input to the server
            additional_payload = {
                "request_id": request_id,
                "additional_input": additional_input
            }
            await websocket.send(str(additional_payload))
            console.print(
                f"[blue]Sent additional input: {additional_input}[/blue]")

            # if additional_input.lower() == 'exit':
            #     await websocket.close()
            #     break
        # except websockets.ConnectionClosed:
            # print("Connection closed, reconnecting...")
            # Break inner loop to reconnect
            await asyncio.sleep(5)
            # websocket = await connect_websocket(WS_URL, request_id)

    except ConnectionClosedOK:
        await websocket.close()


@app.command()
def submit_metadata():
    """Submit metadata to the LLM agent API."""
    user_id = Prompt.ask("User ID")
    session_id = Prompt.ask("Session ID")
    organisation_id = Prompt.ask("Organisation ID")
    project_id = Prompt.ask("Project ID")
    application_id = Prompt.ask("Application ID")
    user_email = Prompt.ask("User Email")
    project_input = Prompt.ask("Project Input")
    usergitid = Prompt.ask("User Git ID")
    task_id = Prompt.ask("Task ID")
    agent_name = Prompt.ask("Agent Name")
    agent_id = Prompt.ask("Agent ID")
    thread_id = Prompt.ask("Thread ID")
    system_process_id = Prompt.ask("System Process ID")

    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "organisation_id": organisation_id,
        "project_id": project_id,
        "application_id": application_id,
        "user_email": user_email,
        "project_input": project_input,
        "usergitid": usergitid,
        "task_id": task_id,
        "agent_name": agent_name,
        "agent_id": agent_id,
        "thread_id": thread_id,
        "system_process_id": system_process_id,
    }

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Submitting metadata...", total=100)
        response = requests.post(f"{API_URL}/metadata", json=payload)
        progress.update(task, advance=100)

    if response.status_code == 200:
        console.print("[green]Metadata submitted successfully![/green]")
    else:
        console.print(f"[red]Failed to submit metadata: {response.text}[/red]")


@app.command()
def submit_project_info():
    """
    Submit project information to the LLM agent and retrieve the enhanced prompt.
    """

    request_id = Prompt.ask("Request ID")
    user_input_prompt_message = Prompt.ask("User Input Prompt Message")

    payload = {
        "request_id": request_id,
        "user_input_prompt_message": user_input_prompt_message,
    }

    console.print("[blue]Submitting project information...[/blue]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Submitting...", total=100)
        post_response = requests.post(f"{API_URL}/project_info", json=payload)
        progress.update(task, advance=100)

    if post_response.status_code == 200:
        console.print(
            f"[green]Project information submitted successfully![/green]")
    else:
        console.print(
            f"[red]Failed to submit project info: {post_response.text}[/red]")
        return

    console.print(
        f"[blue]Waiting for the LLM's enhanced prompt for Request ID: {request_id}...[/blue]")

    #
    max_retries = 300
    retry_interval = 3

    for _ in range(max_retries):
        get_response = requests.get(f"{API_URL}/enhanced_prompt/{request_id}")

        if get_response.status_code == 200:
            enhanced_prompt = get_response.json()
            console.print(f"[green]Enhanced prompt received![/green]")
            console.print(
                f"[yellow]LLM Response: {enhanced_prompt['llm_output_prompt_message_response']}[/yellow]")
            break
        elif get_response.status_code == 404:
            console.print(
                f"[yellow]No enhanced prompt available yet, retrying...[/yellow]")
        else:
            console.print(
                f"[red]Error fetching enhanced prompt: {get_response.text}[/red]")
            break

        asyncio.sleep(retry_interval)

    else:
        console.print(
            f"[red]Max retries reached. Failed to retrieve the enhanced prompt for Request ID: {request_id}.[/red]")


@app.command()
def submit_additional_input():
    """Submit additional input for an ongoing conversation."""
    request_id = Prompt.ask("Request ID")
    user_input_prompt_message = Prompt.ask("User Input Prompt Message")

    payload = {
        "request_id": request_id,
        "user_input_prompt_message": user_input_prompt_message,
    }

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Submitting additional input...", total=100)
        response = requests.post(f"{API_URL}/additional_input", json=payload)
        progress.update(task, advance=100)

    if response.status_code == 200:
        console.print(
            "[green]Additional input submitted successfully![/green]")
    else:
        console.print(
            f"[red]Failed to submit additional input: {response.text}[/red]")


@app.command()
def submit_project_and_listen():
    """
    Submit project information to the LLM agent and retrieve the enhanced prompt via WebSockets.
    """

    request_id = Prompt.ask("Request ID")
    user_input_prompt_message = Prompt.ask("User Input Prompt Message")

    payload = {
        "request_id": request_id,
        "user_input_prompt_message": user_input_prompt_message,
    }

    console.print("[blue]Submitting project information...[/blue]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Submitting...", total=100)
        post_response = requests.post(f"{API_URL}/project_info", json=payload)
        progress.update(task, advance=100)

    if post_response.status_code == 200:
        console.print(
            f"[green]Project information submitted successfully![/green]")
    else:
        console.print(
            f"[red]Failed to submit project info: {post_response.text}[/red]")
        return

    console.print(
        f"[blue]Waiting for the LLM's enhanced prompt for Request ID: {request_id}...[/blue]")

    asyncio.run(listen_for_prompt(request_id))


async def listen_for_prompt(request_id: str):
    """
    Connect to the WebSocket server and listen for the enhanced prompt.
    """
    try:
        async with websockets.connect(f"{WS_URLL}/{request_id}") as websocket:
            console.print(
                "[yellow]Connected to WebSocket... Waiting for the LLM response...[/yellow]")

            while True:

                message = await websocket.recv()
                response = eval(message)

                if response["status"] == "success":

                    console.print(
                        f"[green]LLM Response: {response['llm_response']}[/green]")
                    break
                elif response["status"] == "error":
                    console.print(f"[red]{response['message']}[/red]")
                    break

    except Exception as e:
        console.print(f"[red]WebSocket connection error: {e}[/red]")


if __name__ == "__main__":
    app()
