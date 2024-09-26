"""
"""
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from agents.agent.graph import Graph
from agents.prompt.prompt_agent import PromptAgent
from agents.prompt.prompt_state import PromptState
from configs.project_config import ProjectGraphs


class PromptGraph(Graph[PromptAgent]):
    """
    """

    def __init__(self,  llm: ChatOpenAI, persistance_db_path: str) -> None:
        """"""
        super().__init__(
            ProjectGraphs.prompt.graph_id,
            ProjectGraphs.prompt.graph_name,
            PromptAgent(llm),
            persistance_db_path
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
        """
        returns the current state of the graph.
        """

        return self.agent.state
