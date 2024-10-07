import sqlite3
from datetime import datetime
from typing import Any, Dict

from database.tables.table import Table
from utils.logs.logging_utils import logger


class Conversation(Table):
    """
    Represents a database table for conversation.

    Args:
        connection (sqlite3.Connection): Connection to the SQLite database.
    """
    id: int
    request_id: int
    response_id: int
    user_input_prompt_message: str
    llm_output_prompt_message_response: str
    conversation_id: str
    created_at: datetime
    updated_at: datetime

    def __init__(self, connection: sqlite3.Connection):
        """
        Initializes the conversation table object.

        Args:
            connection (sqlite3.Connection): Connection to the SQLite database.
        """
        self.name = "conversation"
        super().__init__(connection)

    def create(self) -> None:
        """
        Creates the mircoservices table in the database.
        """

        logger.info(f"Creating {self.name} Table...")

        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.name} (
            id INTEGER PRIMARY KEY,
            request_id INTEGER DEFAULT NULL,
            response_id INTEGER DEFAULT NULL,
            conversation_id INTEGER DEFAULT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            user_input_prompt_message TEXT DEFAULT NULL,
            llm_output_prompt_message_response TEXT DEFAULT NULL,
            FOREIGN KEY (conversation_id) REFERENCES metadata (id)
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

    def insert(self, request_id: str = '', response_id: str = '', conversation_id: str = '', user_input_prompt_message: str = '', llm_output_prompt_message_response: str = '') -> Dict[str, Any]:
        """
        Inserts a new metric record into the table and returns it as a dictionary.
        """

        return super().insert(
            request_id=request_id,
            response_id=response_id,
            user_input_prompt_message=user_input_prompt_message,
            llm_output_prompt_message_response=llm_output_prompt_message_response,
            conversation_id=conversation_id
        )

    def __valid_columns__(self) -> set:
        """
        Returns the set of valid columns for the metrics table.
        """
        return {"id", "request_id", "response_id", "user_input_prompt_message", "llm_output_prompt_message_response", "conversation_id", "created_at", "updated_at"}
