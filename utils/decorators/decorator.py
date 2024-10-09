from functools import wraps
from datetime import datetime
from configs.database import get_client_local_db_file_path
from database.database import Database
from genpod.member import AgentMember
from policies.pydantic_models.constants import Status
from agents.supervisor.supervisor_state import SupervisorState
from utils.logs.logging_utils import logger


def measure_execution_time(get_member):
    """
    Decorator to measure the execution time of a function and save it using save_execution_time method.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, state: SupervisorState, *args, **kwargs):
            member: AgentMember = get_member(self)
            start_time = datetime.now()

            try:
                result = func(self, state, *args, **kwargs)
            finally:
                end_time = datetime.now()

            if state['current_task'].task_status == Status.NONE:
                current_task_id = None
            else:
                current_task_id = state['current_task'].task_id

            duration = (end_time - start_time).microseconds

            save_execution_time(state, current_task_id, start_time, end_time,
                                duration, member.member_name, member.member_id)

            return result
        return wrapper
    return decorator


def save_execution_time(state: SupervisorState, task_id, start_time, end_time, duration, agent_name, agent_id) -> int:

    try:
        # Save the metrics to the database
        DATABASE_PATH = get_client_local_db_file_path()
        db = Database(DATABASE_PATH)

        metrics = db.metrics_table.insert(
            state['project_id'],
            state['microservice_id'],
            task_id,
            start_time,
            end_time,
            duration,
            agent_name,
            agent_id)

        return metrics

    except Exception as e:
        logger.error(f"Failed to save execution time. Error: {e}")
