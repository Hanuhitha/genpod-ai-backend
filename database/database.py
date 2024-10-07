import sqlite3

from database.tables.conversation import Conversation
from database.tables.metadata import Metadata
from database.tables.metrics import Metrics

from database.tables.microservices import Microservices
from database.tables.projects import Projects
from database.tables.sessions import Sessions
from database.tables.tokens import Tokens
from utils.logs.logging_utils import logger


class Database():
    """
    A simple SQLite database wrapper.

    Args:
        db_path (str): Path to the SQLite database file.
    """

    db_path: str

    connection: sqlite3.Connection
    cursor: sqlite3.Cursor

    # tables
    projects_table: Projects
    microservices_table: Microservices
    sessions_table: Sessions
    metrics_table: Metrics
    conversation_table: Conversation
    metadata_table: Metadata

    def __init__(self, db_path):
        """
        Initializes the Database object.

        Args:
            db_path (str): Path to the SQLite database file.
        """

        self.db_path = db_path

        self.connection = self.connect()
        self.cursor = self.connection.cursor()

        # Initialize table instances
        self.projects_table = Projects(self.connection)
        self.microservices_table = Microservices(self.connection)
        self.sessions_table = Sessions(self.connection)
        self.metrics_table = Metrics(self.connection)
        self.tokens_table = Tokens(self.connection)
        self.metadata_table = Metadata(self.connection)
        self.conversation_table = Conversation(self.connection)

    def connect(self) -> sqlite3.Connection:
        """
        Establishes a connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection to the database.
        """

        try:
            logger.info(
                f"Connecting to the database at path: `{self.db_path}`")

            sqCon = sqlite3.connect(self.db_path)
            logger.info(f"Database connection successful.")

            return sqCon

        except sqlite3.Error as sqe:
            logger.error(
                f"Error occurred while connecting to SQLite with db `{self.db_path}`: {sqe}")
            raise

    def setup_db(self):
        """
        Creates necessary tables in the database.
        """

        logger.info("Creating database tables...")

        try:
            # Create projects table
            self.projects_table.create()

            # Create microservice table
            self.microservices_table.create()

            # Create sessions table
            self.sessions_table.create()

            # Create metrics table
            self.metrics_table.create()

            #  Create tokens table
            self.tokens_table.create()

            # Create metadata table
            self.metadata_table.create()

            # Create conversation table
            self.conversation_table.create()

            self.connection.commit()
        except sqlite3.Error as sqe:
            logger.error(f"Error Occured while creating tables: {sqe}")
            raise

    def close(self):
        """
        Closes the database connection.
        """

        self.connection.close()
        self.cursor.close()
        logger.info("Database connection closed")

    def insert_into_projects(con: sqlite3.Connection, project_name: str, input_prompt: str) -> Projects:
        """
        """
