import sqlite3
from datetime import datetime
from typing import Any, Dict

from database.tables.table import Table
from utils.logs.logging_utils import logger


class Projects(Table):
    """
    Represents a database table for projects.

    Args:
        connection (sqlite3.Connection): Connection to the SQLite database.
    """
    id: int # unique identifier of the record
    project_name: str # name of the project
    input_prompt: str # input prompt used for the project
    status: str # status of the project generation
    license_text: str # user given license text for the project
    license_file_url: str # user given license file url
    project_location: str # path where project is located
    created_at: datetime # timestamp of when record is created
    updated_at: datetime # timestamp of the records last update
    created_by: int # user id of who created the record
    updated_by: int # user id of the who has updated this record at last

    def __init__(self, connection: sqlite3.Connection):
        """
        Initializes the Projects table object.

        Args:
            connection (sqlite3.Connection): Connection to the SQLite database.
        """
        self.name = "projects"
        
        super().__init__(connection)

    def create(self) -> None:
        """
        Creates the projects table in the database.
        """

        logger.info(f"Creating {self.name} Table...")

        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.name} (
            id INTEGER PRIMARY KEY UNIQUE,
            project_name TEXT NOT NULL,
            input_prompt TEXT NOT NULL,
            status TEXT NOT NULL,
            license_text TEXT,
            license_file_url TEXT,
            project_location TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            created_by INTEGER NOT NULL,
            updated_by INTEGER NOT NULL
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
    
    def insert(self, project_name: str, input_prompt: str, status: str, project_location: str, user_id: int, license_text: str="", license_file_url: str="") -> Dict[str, Any]:
        """
        """

        return super().insert(
            project_name=project_name,
            input_prompt=input_prompt,
            status=status,
            project_location=project_location,
            license_text=license_text,
            license_file_url=license_file_url,
            created_by=user_id,
            updated_by=user_id
        )

    def __valid_columns__(self) -> set:
        """
        Returns the set of valid columns for the microservices table.
        """
        return {"id", "project_name", "input_prompt", "status", "license_text", "license_file_url", "project_location", "created_at", "updated_at", "created_by", "updated_by"}