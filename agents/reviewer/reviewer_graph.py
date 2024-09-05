"""
"""
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

from agents.agent.graph import Graph
from agents.reviewer.reviewer_agent import ReviewerAgent
from agents.reviewer.reviewer_state import ReviewerState
from configs.project_config import ProjectGraphs


class ReviewerGraph(Graph[ReviewerAgent]):
    """
    """

    def __init__(self,  llm: ChatOpenAI, persistance_db_path: str) -> None:
        """"""
        super().__init__(
            ProjectGraphs.reviewer.graph_id,
            ProjectGraphs.reviewer.graph_name, 
            ReviewerAgent(llm),
            persistance_db_path
        )

        self.compile_graph_with_persistence()

    def define_graph(self) -> StateGraph:
        
        reviewer_flow = StateGraph(ReviewerState)

        return reviewer_flow
        
    
    def get_current_state(self) -> ReviewerState:
        """
        returns the current state of the graph.
        """
        
        return self.agent.state
    