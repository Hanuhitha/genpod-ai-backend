from agents.architect.architect_graph import ArchitectGraph
from agents.architect.architect_state import ArchitectState
from configs.project_config import ProjectAgents, ProjectConfig
from genpod.member import AgentMember


class ArchitectMember(AgentMember[ArchitectState, ArchitectGraph]):
    """
    """

    def __init__(self, persistance_db_path: str):
        """"""

        self.architect_config = ProjectConfig().agents_config[ProjectAgents.architect.agent_id]
        super().__init__(
            self.architect_config, 
            ArchitectState, 
            ArchitectGraph(self.architect_config.llm, persistance_db_path)
        )
