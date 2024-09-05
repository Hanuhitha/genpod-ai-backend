import sqlite3
from datetime import datetime
from typing import Any, Dict

from database.tables.table import Table
from utils.logs.logging_utils import logger


class Microservices(Table):
    """
    Represents a database table for microservices.

    Args:
        connection (sqlite3.Connection): Connection to the SQLite database.
    """
    id: int # unique identifier of the record
    microservice_name: str # name of the microservice
    project_id: int # id of the project to which this microservice belongs to
    status: str # status of this microservice generation
    created_at: datetime # timestamp of when record is created
    updated_at: datetime # timestamp of the records last update
    created_by: int # user id of who created the record
    updated_by: int # user id of the who has updated this record at last
    
    def __init__(self, connection: sqlite3.Connection):
        """
        Initializes the Sessions table object.
        
        Args:
            connection (sqlite3.Connection): Connection to the SQLite database.
        """
        self.name = "microservices"
        super().__init__(connection)

    def create(self) -> None:
        """
        Creates the mircoservices table in the database.
        """

        logger.info(f"Creating {self.name} Table...")

        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.name} (
            id INTEGER PRIMARY KEY UNIQUE,
            microservice_name TEXT NOT NULL,
            project_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            created_by TEXT NOT NULL,
            updated_by TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id)
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
        
    def insert(self, microservice_name: str, project_id: str, status: str, user_id: str) -> Dict[str, Any]:
        """
        """

        return super().insert(
            microservice_name=microservice_name,
            project_id=project_id,
            status=status,
            created_by=user_id,
            updated_by=user_id
        )

    def __valid_columns__(self) -> set:
        """
        Returns the set of valid columns for the microservices table.
        """
        return {"id", "microservice_name", "project_id", "status", "created_at", "updated_at", "created_by", "updated_by"}