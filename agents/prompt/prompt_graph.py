# """
# """
# from langchain_openai import ChatOpenAI
# from langgraph.graph import StateGraph

# from agents.agent.graph import Graph
# from agents.prompt.prompt_agent import PromptAgent
# from agents.prompt.prompt_state import PromptState
# from configs.project_config import ProjectGraphs


# class PromptGraph(Graph[PromptAgent]):
#     """
#     """

#     def __init__(self,  llm: ChatOpenAI, persistance_db_path: str) -> None:
#         """"""
#         super().__init__(
#             ProjectGraphs.prompt.graph_id,
#             ProjectGraphs.prompt.graph_name, 
#             PromptAgent(llm),
#             persistance_db_path
#         )

#         self.compile_graph_with_persistence()

#     def define_graph(self) -> StateGraph:
        
#         prompt_flow = StateGraph(PromptState)

#         return prompt_flow
        
    
#     def get_current_state(self) -> PromptState:
#         """
#         returns the current state of the graph.
#         """
        
#         return self.agent.state
    