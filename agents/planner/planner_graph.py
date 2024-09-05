from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from agents.agent.graph import Graph
from agents.planner.planner_agent import PlannerAgent
from agents.planner.planner_state import PlannerState
from configs.project_config import ProjectGraphs
from models.models import Task


class PlannerWorkFlow(Graph[PlannerAgent]):
    def __init__(self, llm: ChatOpenAI, persistance_db_path: str):
        super().__init__(
            ProjectGraphs.planner.graph_id,
            ProjectGraphs.planner.graph_name, 
            PlannerAgent(llm),
            persistance_db_path
        )

        self.compile_graph_with_persistence()

    def define_graph(self) -> StateGraph:
        
        planner_workflow = StateGraph(PlannerState, config_schema=Task)
        # Define the nodes
        # self.planner_workflow.add_node("new_deliverable_check", self.agent.new_deliverable_check)
        planner_workflow.add_node("backlog_planner", self.agent.backlog_planner)  # retrieve
        planner_workflow.add_node("requirements_developer", self.agent.requirements_developer)  # grade documents
        planner_workflow.add_node("response_generator",self.agent.generate_response)
        planner_workflow.add_node("update_state", self.agent.update_state)

        # Build graph
        planner_workflow.set_conditional_entry_point(self.agent.new_deliverable_check,
                                                          {"backlog_planner": "backlog_planner",
                                                           "requirements_developer": "requirements_developer"})

        # self.planner_workflow.set_conditional_entry_point(
        #     self.agent.new_deliverable_check,
        #     {
        #         "yes": "backlog_planner",
        #         "no": "requirements_developer"
        #     }
        # )
        planner_workflow.add_edge("backlog_planner", "requirements_developer")
        planner_workflow.add_edge("requirements_developer", "update_state")
        planner_workflow.add_edge("update_state","response_generator")
        planner_workflow.add_edge("response_generator", END)

        return planner_workflow
    
    def get_current_state(self):
        """ Returns the current state dictionary of the agent """
        return self.agent.state

    def update_task(self, incoming_task: Task):
        try:
            self.agent.current_task = incoming_task
            return "Successfully added the task to memory"
        except: 
            return "Unable to add the task to memory"
