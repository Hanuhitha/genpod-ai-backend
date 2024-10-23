import io
from typing import Generic, TypeVar

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph.graph import StateGraph
from langgraph.graph.graph import CompiledGraph
from PIL import Image
from typing_extensions import Any

GenericAgent = TypeVar('GenericAgent', bound=Any)


class Graph(Generic[GenericAgent]):
    """
    Base class for defining and managing state graphs.

    Attributes:
        id (str): Unique identifier for the graph.
        name (str): Name of the graph.
        agent (GenericAgent): The agent associated with the graph.
        memory (SqliteSaver/AsyncSqliteSaver): The persistence mechanism for saving the graph state.
        app (CompiledGraph): The compiled state graph.
    """

    name: str
    id: str

    agent: GenericAgent
    memory: SqliteSaver
    app: CompiledGraph

    def __init__(self, id: str, name: str, agent: GenericAgent, persistence_db_path: str, is_async: bool = False) -> None:
        """
        Constructor for the Graph class.

        Args:
            id (str): Unique identifier for the graph.
            name (str): Name of the graph.
            agent (GenericAgent): The agent associated with the graph.
            persistence_db_path (str): Path to the SQLite database for persistence.
        """
        self.id = id
        self.name = name
        self.agent = agent
        self.is_async = is_async
        self.memory = AsyncSqliteSaver.from_conn_string(
            persistence_db_path) if self.is_async else SqliteSaver.from_conn_string(persistence_db_path)
        # self.memory = None if self.is_async else SqliteSaver.from_conn_string(
        # persistence_db_path)
        self.app = None

    def compile_graph_with_persistence(self) -> None:
        """
        Compiles the graph defined by `define_graph` and persists it using `SqliteSaver`.
        """
        if self.app is None:
            self.app = self.define_graph().compile(checkpointer=self.memory)
        else:
            raise RuntimeError("Graph has already been compiled.")

    def display_graph(self) -> None:
        """
        Displays the graph visually. The graph is rendered as an image and shown.
        """
        if self.app is None:
            raise RuntimeError("Graph has not been compiled yet.")

        try:
            img = Image.open(io.BytesIO(
                self.app.get_graph().draw_mermaid_png()))
            img.show()
        except Exception as e:
            print(f"Failed to display graph: {e}")

    def define_graph(self) -> StateGraph:
        """
        Defines the state graph for the agent. Must be implemented by subclasses.

        Returns:
            StateGraph: The state graph for the agent.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def get_current_state(self) -> Any:
        """
        Fetches the current state of the graph. Must be implemented by subclasses.

        Returns:
            Any: The current state of the agent.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def __repr__(self) -> str:
        """
        Provides a string representation of the Graph instance.

        Returns:
            str: A string representation of the Graph instance.
        """
        return f"Graph(id={self.id}, name={self.name}, agent={self.agent})"
