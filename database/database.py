import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database_base import Base
from database.tables.metrics import Metrics
from database.tables.microservices import Microservices
from database.tables.projects import Projects
from database.tables.sessions import Sessions
from database.tables.tokens import Tokens
from utils.logs.logging_utils import logger
from database.tables.conversation import Conversation  # SQLAlchemy ORM Model
from database.tables.metadata import Metadata  # SQLAlchemy ORM Model
from sqlalchemy.ext.declarative import declarative_base

# Define the Base class for SQLAlchemy ORM models
Base = declarative_base()


class Database():
    """
    A hybrid SQLite database wrapper that uses SQLAlchemy ORM for specific tables (Conversation, Metadata)
    and sqlite3 for others.


    Args:
        db_path (str): Path to the SQLite database file.
    """

    db_path: str

    connection: sqlite3.Connection
    cursor: sqlite3.Cursor

    # SQLAlchemy session factory and engine for ORM tables
    engine = None
    SessionLocal = None

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

        # Initialize SQLAlchemy engine and session for ORM tables
        self.engine = create_engine(
            f'sqlite:///{self.db_path}', connect_args={"check_same_thread": False})

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)

        # Initialize table instances
        self.projects_table = Projects(self.connection)
        self.microservices_table = Microservices(self.connection)
        self.sessions_table = Sessions(self.connection)
        self.metrics_table = Metrics(self.connection)
        self.tokens_table = Tokens(self.connection)
        self.metadata_table = Metadata
        self.conversation_table = Conversation

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
            sqCon.row_factory = sqlite3.Row
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

            Base.metadata.create_all(bind=self.engine)

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
            # self.metadata_table.create()

            # # Create conversation table
            # self.conversation_table.create()

            self.connection.commit()

        except sqlite3.Error as sqe:
            logger.error(f"Error Occured while creating tables: {sqe}")
            raise

        except Exception as e:
            logger.error(f"Error Occurred while creating ORM tables: {e}")
            raise

    def close(self):
        """
        Closes the database connection.
        """

        self.connection.close()
        self.cursor.close()
        logger.info("SQLite connection closed")

        # Close SQLAlchemy session
        if self.SessionLocal:
            self.SessionLocal().close()
        logger.info("SQLAlchemy session closed")

    def insert_into_projects(self, project_name: str, input_prompt: str):
        """
        Inserts data into the projects table using raw SQLite.
        """
