import sqlite3
from datetime import datetime
from typing import Any, Dict

from database.tables.table import Table
from utils.logs.logging_utils import logger


class Metadata(Table):
    """
    Represents a database table for metadata.

    Args:
        connection (sqlite3.Connection): Connection to the SQLite database.
    """
    id: int
    user_id: int
    session_id: int
    organisation_id: int
    project_id: int
    application_id: int
    user_email: str
    project_input: str
    usergitid: str
    task_id: int
    agent_name: str
    agent_id: str
    thread_id: str
    system_process_id: int
    created_at: datetime
    updated_at: datetime

    def __init__(self, connection: sqlite3.Connection):
        """
        Initializes the metadata table object.

        Args:
            connection (sqlite3.Connection): Connection to the SQLite database.
        """
        self.name = "metadata"
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
            user_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            organisation_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            user_email TEXT NOT NULL,
            project_input TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            application_id INTEGER NOT NULL,
            usergitid INTEGER NOT NULL,
            thread_id INTEGER NOT NULL,
            system_process_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
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

    def insert(self, project_id: int, user_id: int, session_id: int, organisation_id: int, application_id: int, user_email: str, project_input: str, usergitid: int, thread_id: int, system_process_id: int, task_id: int, agent_name: str, agent_id: str) -> Dict[str, Any]:
        """
        Inserts a new metric record into the table and returns it as a dictionary.
        """

        return super().insert(
            project_id=project_id,
            user_id=user_id,
            session_id=session_id,
            organisation_id=organisation_id,
            application_id=application_id,
            user_email=user_email,
            project_input=project_input,
            usergitid=usergitid,
            thread_id=thread_id,
            system_process_id=system_process_id,
            task_id=task_id,
            agent_name=agent_name,
            agent_id=agent_id

        )

    def __valid_columns__(self) -> set:
        """
        Returns the set of valid columns for the metrics table.
        """
        return {"id", "project_id", "user_id", "session_id", "organisation_id", "application_id", "user_email", "project_input", "usergitid", "thread_id", "system_process_id", "task_id", "agent_name", "agent_id"}
