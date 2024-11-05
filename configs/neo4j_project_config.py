import os
from neo4j import GraphDatabase

from configs.project_config import AGENTS_CONFIG, ProjectAgents, ProjectGraphs


class ProjectConfig:
    """
    Configuration for the entire project, including agent configurations, vector database settings, and Neo4j.
    """

    def __init__(self) -> None:
        """
        Initializes the project configuration with predefined agents, their configurations,
        vector database collection paths, and Neo4j connection settings.
        """
        # Initialize existing configurations
        self.graphs = ProjectGraphs
        self.agents = ProjectAgents
        self.agents_config = AGENTS_CONFIG
        self.collection_name = "MISMO-version-3.6-docs"
        self.vector_db_collections = {
            'MISMO-version-3.6-docs': os.path.join(os.getcwd(), "vector_collections")
        }

        # Neo4j configuration
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "your_password")
        self.neo4j_driver = self.init_neo4j_driver()

    def init_neo4j_driver(self):
        """
        Initializes and returns the Neo4j driver.

        Returns:
            Neo4j driver instance for interacting with the Neo4j database.
        """
        return GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_username, self.neo4j_password)
        )

    def close_neo4j_driver(self):
        """
        Closes the Neo4j driver connection.
        """
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def __del__(self):
        """
        Destructor to ensure Neo4j driver is closed when ProjectConfig is deleted.
        """
        self.close_neo4j_driver()
