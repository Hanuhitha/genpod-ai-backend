from pprint import pprint

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from agents.planner.planner_graph import PlannerWorkFlow
from policies.models.models import Status, Task

load_dotenv()

if __name__ == "__main__":
    #  Example using in you main graph.

    llm = ChatOpenAI(model="gpt-4o-2024-05-13", temperature=0,
                     max_retries=5, streaming=True, seed=4000)

    planner_thread_id = "3"
    Planner = PlannerWorkFlow(llm=llm, thread_id=planner_thread_id)

    init_task = Task(description="Implement REST API endpoints for 'User resource'.", task_status=Status.NEW.value, additional_info='**REST API Endpoints**: The service should provide the following endpoints for the `User` resource:\n- `POST /users`: Create a new '
                     'user.\n- `GET /users`: List all users.\n- `GET /users/{id}`: Get a specific user by ID.\n- `PUT /users/{id}`: Update a specific user by ID.\n- `DELETE /users/{id}`: Delete a specific user by ID.\n', question='')

    awating_task = Task(description="Implement REST API endpoints for 'User resource'.", task_status=Status.AWAITING.value, additional_info='**REST API Endpoints**: The service should provide the following endpoints for the `User` resource:\n- `POST /users`: Create a new '
                        'user.\n- `GET /users`: List all users.\n- `GET /users/{id}`: Get a specific user by ID.\n- `PUT /users/{id}`: Update a specific user by ID.\n- `DELETE /users/{id}`: Delete a specific user by ID.\n', question='')

    response = Planner.update_task(init_task)
    # response = Planner.update_task(awating_task)

    config = {"configurable": {"thread_id": planner_thread_id}}

    result = Planner.planner_app.invoke(
        {"deliverable": "Implement REST API endpoints for 'User resource'."}, config)

    pprint(result)
