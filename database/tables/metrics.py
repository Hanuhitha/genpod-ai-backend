import sqlite3
from datetime import datetime
from typing import Any, Dict

from database.tables.table import Table
from utils.logs.logging_utils import logger


class Metrics(Table):
    """
    Represents a database table for metrics.

    Args:
        connection (sqlite3.Connection): Connection to the SQLite database.
    """
    id: int
    project_id: int
    microservice_id: int
    task_id: int
    start_time: datetime
    end_time: datetime
    duration: float
    agent_name: str
    agent_id: str
    created_at: datetime
    updated_at: datetime

    def __init__(self, connection: sqlite3.Connection):
        """
        Initializes the metrics table object.

        Args:
            connection (sqlite3.Connection): Connection to the SQLite database.
        """
        self.name = "metrics"
        super().__init__(connection)

    def create(self) -> None:
        """
        Creates the mircoservices table in the database.
        """

        logger.info(f"Creating {self.name} Table...")

        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.name} (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            microservice_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            duration FLOAT NOT NULL,
            agent_name TEXT NOT NULL,
            agent_id TEXT NOT NULL
        );
        '''
        try:
            cursor = self.connection.cursor()

            cursor.execute(create_table_query)
            logger.info(f"{self.name} table created successfully.")

            self.connection.commit()
        except sqlite3.Error as sqe:
            logger.error(f"Error creating {self.name} table: {sqe}")
            raise
        finally:
            if cursor:
                cursor.close()

    def insert(self, project_id: str, microservice_id: str, task_id: str, start_time: str, end_time: str, duration: str, agent_name: str, agent_id: str) -> Dict[str, Any]:
        """
        Inserts a new metric record into the table and returns it as a dictionary.
        """

        return super().insert(
            project_id=project_id,
            microservice_id=microservice_id,
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            agent_name=agent_name,
            agent_id=agent_id
        )

    def __valid_columns__(self) -> set:
        """
        Returns the set of valid columns for the metrics table.
        """
        return {"id", "project_id", "microservice_id", "task_id", "created_at", "updated_at", "start_time", "end_time", "duration", "agent_name", "agent_id"}
