"""
"""
from fastapi import WebSocket
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from agents.agent.graph import Graph
from agents.prompt_agent.prompt_agent import PromptAgent
from agents.prompt_agent.prompt_state import PromptState
from configs.project_config import ProjectConfig, ProjectGraphs


class PromptGraph(Graph[PromptAgent]):
    """
    A graph class that uses Neo4j for persistence in managing the state and flow of the PromptAgent.
    """

    def __init__(self,  llm: ChatOpenAI, persistance_db_path: str, websocket: WebSocket, is_async: bool) -> None:
        """
        Initializes the PromptGraph with Neo4j persistence.

        Args:
            llm (ChatOpenAI): The language model.
            websocket (WebSocket): The WebSocket connection.
            is_async (bool): Whether the graph should operate asynchronously.
            project_config (ProjectConfig): Project configuration containing Neo4j driver.
        """
        # self.neo4j_driver = project_config.neo4j_driver  # Neo4j driver from ProjectConfig

        super().__init__(
            ProjectGraphs.prompt.graph_id,
            ProjectGraphs.prompt.graph_name,
            PromptAgent(llm, websocket),
            persistance_db_path,
            is_async=is_async
        )

        self.compile_graph_with_persistence()

    def define_graph(self) -> StateGraph:

        prompt_flow = StateGraph(PromptState)

        # node
        prompt_flow.add_node(self.agent.prompt_node_name, self.agent.chat_node)
        prompt_flow.add_node(
            self.agent.refined_prompt_node_name, self.agent.refined_prompt_node)

        # edges
        prompt_flow.add_conditional_edges(
            self.agent.prompt_node_name,
            self.agent.router,
            {
                self.agent.prompt_node_name: self.agent.prompt_node_name,
                self.agent.refined_prompt_node_name: self.agent.refined_prompt_node_name,
            }

        )
        prompt_flow.add_edge(self.agent.refined_prompt_node_name, END)

        # entry point
        prompt_flow.set_entry_point(self.agent.prompt_node_name)

        return prompt_flow
    
    def get_current_state(self) -> PromptState:
        # returns the current state of the graph.
        return self.agent.state

    # def save_state_to_neo4j(self, state: PromptState):
    #     """
    #     Saves the current state of the prompt agent to Neo4j.

    #     Args:
    #         state (PromptState): The state of the prompt agent.
    #     """
    #     with self.neo4j_driver.session() as session:
    #         query = """
    #         MERGE (p:PromptState {request_id: $request_id})
    #         SET p.original_user_input = $original_user_input,
    #             p.messages = $messages,
    #             p.status = $status
    #         RETURN p
    #         """
    #         parameters = {
    #             "request_id": state["request_id"],
    #             "original_user_input": state["original_user_input"],
    #             "messages": state["messages"],
    #             "status": state["status"]
    #         }
    #         session.run(query, parameters)

    # def get_current_state_from_neo4j(self, request_id: int) -> PromptState:
    #     """
    #     Retrieves the current state of the prompt agent from Neo4j.

    #     Args:
    #         request_id (int): The ID of the request.

    #     Returns:
    #         PromptState: The current state of the prompt agent.
    #     """
    #     with self.neo4j_driver.session() as session:
    #         query = """
    #         MATCH (p:PromptState {request_id: $request_id})
    #         RETURN p.original_user_input AS original_user_input,
    #                p.messages AS messages,
    #                p.status AS status,
    #                p.request_id AS request_id
    #         """
    #         parameters = {"request_id": request_id}
    #         result = session.run(query, parameters)

    #         record = result.single()
    #         if record:
    #             return PromptState(
    #                 original_user_input=record["original_user_input"],
    #                 messages=record["messages"],
    #                 status=record["status"],
    #                 request_id=record["request_id"]
    #             )
    #         return None
