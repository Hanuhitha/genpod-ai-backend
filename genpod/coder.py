from agents.coder.coder_graph import CoderGraph
from agents.coder.coder_state import CoderState
from configs.project_config import ProjectAgents, ProjectConfig
from genpod.member import AgentMember


class CoderMember(AgentMember[CoderState, CoderGraph]):
    """
    """

    def __init__(self, persistance_db_path: str):
        """"""

        self.coder_config = ProjectConfig().agents_config[ProjectAgents.coder.agent_id]
        super().__init__(
            self.coder_config, 
            CoderState, 
            CoderGraph(self.coder_config.llm, persistance_db_path)
        )
    