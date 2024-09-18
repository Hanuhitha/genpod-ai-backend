from agents.tests_generator.tests_generator_graph import TestCoderGraph
from agents.tests_generator.tests_generator_state import TestCoderState
from configs.project_config import ProjectAgents, ProjectConfig
from genpod.member import AgentMember


class TestsGeneratorMember(AgentMember[TestCoderState, TestCoderGraph]):
    """
    """

    def __init__(self, persistance_db_path: str):
        """"""

        self.tests_generator_config = ProjectConfig().agents_config[ProjectAgents.tests_generator.agent_id]
        super().__init__(
            self.tests_generator_config, 
            TestCoderState, 
            TestCoderGraph(self.tests_generator_config.llm, persistance_db_path)
        )
