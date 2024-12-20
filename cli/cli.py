# cli/cli.py

import typer
import requests
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import time
import websockets
from websockets.asyncio.client import connect
import json
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



# async def connect_websocket(WS_URL: str, request_id: str, max_retries: int = 5):
#     """Connect to WebSocket with retries using exponential backoff."""
#     attempt = 0
#     websocket = None

#     while attempt < max_retries:
#         try:
#             console.print(f"[INFO] Attempting to connect to WebSocket... (Attempt {attempt + 1}/{max_retries})")
#             websocket = await connect(
#                 f"{WS_URL}/{request_id}",
#                 ping_interval=20,  # Send ping every 20 seconds
#                 ping_timeout=30    # Wait 30 seconds for a pong response
#             )
#             console.print("[SUCCESS] Connected to WebSocket!")
#             return websocket
#         except websockets.exceptions.ConnectionClosedError as e:
#             console.print(f"[WARNING] Connection failed: {e}")
#             attempt += 1
#             wait_time = min(2 ** attempt, 60)
#             console.print(f"[INFO] Reconnecting in {wait_time} seconds... (Attempt {attempt}/{max_retries})")
#             await asyncio.sleep(2 ** attempt) 
#     console.print("[ERROR] Maximum retries reached. Could not connect to WebSocket.")
#     return None  


# async def websocket_conversation(request_id: str, user_input_prompt_message: str):
#     """
#     WebSocket connection to submit project info and handle conversation with the server.
#     """
#     continue_connection = False

#     try:
#         websocket = await connect_websocket(WS_URL, request_id)
#         console.print(
#             f"[yellow]Connected to WebSocket for Request ID: {request_id}[/yellow]")

#         # Step 1: Send the initial project info to the WebSocket server
#         project_payload = {
#             "request_id": request_id,
#             "user_input_prompt_message": user_input_prompt_message
#         }
#         post_response = requests.post(
#             f"{API_URL}/project_info", json=project_payload)
#         if post_response.status_code == 200:
#             console.print(
#                 f"[green]Project information submitted successfully![/green]")
#         else:
#             console.print(
#                 f"[red]Failed to submit project info: {post_response.text}[/red]")
#             return
#         await websocket.send(str(project_payload))
#         console.print(
#             f"[blue]Sent project input: {user_input_prompt_message}[/blue]")

#         # Step 2: Wait for the server's response (via FastAPI and the Prompt Agent)
#         while True:
#             # await websocket.send("ping")  # Send a keep-alive ping
#             # await asyncio.sleep(5)  # Adjust interval as needed

#             # try:
#             response = await websocket.recv()
#             print(response)
#             response = eval(response)

#             if 'enhanced_prompt' in response:
#                 console.print(
#                     f"[green]Server Response: {response['enhanced_prompt']}[/green]")
#             if 'decision' in response:
#                 if response['decision'] == 'YES':
#                     await websocket.close()
#                     break

#             if 'response' in response:
#                 console.print(
#                     f"[red]Server Response: {response['response']}[/red]")
#             # Ask if the user wants to provide additional input
#             additional_input = Prompt.ask(
#                 "Provide additional input (or type 'yes' to stop)")

#             # Send additional input to the server
#             additional_payload = {
#                 "request_id": request_id,
#                 "additional_input": additional_input
#             }
#             await websocket.send(str(additional_payload))
#             console.print(
#                 f"[blue]Sent additional input: {additional_input}[/blue]")

#             await asyncio.sleep(5)

#     except ConnectionClosedOK:
#         await websocket.close()


async def connect_websocket(WS_URL: str, request_id: str, max_retries: int = 5):
    """Connect to WebSocket with retries using exponential backoff."""
    attempt = 0
    websocket = None

    while attempt < max_retries:
        try:
            console.print(f"[INFO] Attempting to connect to WebSocket... (Attempt {attempt + 1}/{max_retries})")
            websocket = await connect(
                f"{WS_URL}/{request_id}",
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=30    # Wait 30 seconds for a pong response
            )
            console.print("[SUCCESS] Connected to WebSocket!")
            return websocket
        except websockets.exceptions.ConnectionClosedError as e:
            console.print(f"[WARNING] Connection failed: {e}")
        except Exception as e:
            console.print(f"[ERROR] Unexpected error occurred: {e}")
        
        attempt += 1
        wait_time = min(2 ** attempt, 60)  # Exponential backoff, capped at 60 seconds
        console.print(f"[INFO] Reconnecting in {wait_time} seconds... (Attempt {attempt}/{max_retries})")
        await asyncio.sleep(wait_time)

    console.print("[ERROR] Maximum retries reached. Could not connect to WebSocket.")
    if websocket:
        await websocket.close()
    return None

async def websocket_conversation(request_id: str, user_input_prompt_message: str):
    """
    WebSocket connection to submit project info and handle conversation with the server.
    """
    max_retries = 5  # Max retries for connection
    attempt = 0      # Retry attempts

    while attempt < max_retries:
        try:
            websocket = await connect_websocket(WS_URL, request_id, max_retries=5)
            if websocket is None:
                console.print("[ERROR] Could not establish a WebSocket connection.")
                break

            console.print(f"[yellow]Connected to WebSocket for Request ID: {request_id}[/yellow]")

            # Step 1: Send the initial project info to the WebSocket server
            project_payload = {
                "request_id": request_id,
                "user_input_prompt_message": user_input_prompt_message
            }
            post_response = requests.post(f"{API_URL}/project_info", json=project_payload)
            if post_response.status_code == 200:
                console.print(f"[green]Project information submitted successfully![/green]")
            else:
                console.print(f"[red]Failed to submit project info: {post_response.text}[/red]")
                return

            await websocket.send(str(project_payload))
            console.print(f"[blue]Sent project input: {user_input_prompt_message}[/blue]")

            while True:
                try:
                    await websocket.send(json.dumps({"type": "ping", "message": "Keep-alive ping from client"}))
                    console.print("[INFO] Sent ping to server to keep connection alive")

                    response = await asyncio.wait_for(websocket.recv(), timeout=30)
                    response = eval(response)

                    if 'enhanced_prompt' in response:
                        console.print(f"[green]Server Response: {response['enhanced_prompt']}[/green]")

                    if 'decision' in response and response['decision'] == 'YES':
                        await websocket.close()
                        break

                    if 'response' in response:
                        console.print(f"[red]Server Response: {response['response']}[/red]")

                    # Ask for additional input
                    additional_input = Prompt.ask("Provide additional input (or type 'yes' to stop)")

                    additional_payload = {
                        "request_id": request_id,
                        "additional_input": additional_input
                    }
                    await websocket.send(str(additional_payload))
                    console.print(f"[blue]Sent additional input: {additional_input}[/blue]")

                    await asyncio.sleep(20)  # Wait before sending the next ping

                except asyncio.TimeoutError:
                    console.print("[ERROR] Timeout waiting for server response. Closing connection.")
                    break

        except ConnectionClosedOK:
            console.print("[INFO] Server closed connection cleanly. Closing WebSocket.")
            break

        except websockets.exceptions.ConnectionClosedError as e:
            console.print(f"[ERROR] Connection closed unexpectedly: {e}")
            attempt += 1
            wait_time = min(2 ** attempt, 60)  # Exponential backoff, capped at 60s
            console.print(f"[INFO] Reconnecting in {wait_time} seconds... (Attempt {attempt}/{max_retries})")
            await asyncio.sleep(wait_time)

        except Exception as e:
            console.print(f"[ERROR] Unexpected error occurred: {e}")
            break

        finally:
            if 'websocket' in locals():
                await websocket.close()

    console.print("[ERROR] Max retries reached. Could not connect to WebSocket.")


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
