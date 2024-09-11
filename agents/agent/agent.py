from typing import Generic, TypeVar

from langchain_openai import ChatOpenAI
from typing_extensions import Any

GenericAgentState = TypeVar('GenericAgentState', bound=Any)
GenericPrompts = TypeVar('GenericPrompts', bound=Any)


class Agent(Generic[GenericAgentState, GenericPrompts]):
    """
    Represents an agent equipped with a language learning model (LLM) that can perform various tasks.

    Attributes:
        agent_id (str): A unique identifier for the agent, typically a combination of ID and name.
        agent_name (str): The name of the agent.
        description (str): A brief description of the agent's purpose or functionality.
        state (Any): The current state of the agent, which can be of any type.
        llm (ChatOpenAI): The language learning model used by the agent, which can be ChatOpenAI model.
    """

    agent_id: str  # Unique identifier for the agent
    agent_name: str  # Name of the agent
    description: str  # Description of the agent's functionality

    state: GenericAgentState  # Current state of the agent
    prompts: GenericPrompts
    llm: ChatOpenAI  # This is the language learning model (llm) for the agent.

    def __init__(self, agent_id: str, agent_name: str, state: GenericAgentState, prompts: GenericPrompts, llm: ChatOpenAI) -> None:
        """
        Initializes the Agent with the specified parameters.

        Args:
            agent_id (str): The unique identifier for the agent.
            agent_name (str): The name of the agent.
            state (Any): The initial state of the agent.
            llm (ChatOpenAI): The language learning model used by the agent.
        """

        self.agent_id = agent_id
        self.agent_name = agent_name
        self.state = state
        self.prompts = prompts
        self.llm = llm

    def update_state(self, state: GenericAgentState) -> GenericAgentState:
        """
        Updates the current state of the agent with the provided state.

        Args:
            state (Any): The new state to update the current state of the agent with.

        Returns:
            Any: The updated state of the agent.
        """

        self.state = {**state}
        return {**self.state}

    def __repr__(self) -> str:
        """
        Provides a string representation of the Agent instance.

        Returns:
            str: A string representation of the Agent instance.
        """
        return f"Agent(id={self.agent_id}, name={self.agent_name}, state={self.state})"
