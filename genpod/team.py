from genpod.architect import ArchitectMember
from genpod.coder import CoderMember
from genpod.member import AgentMember
from genpod.planner import PlannerMember
from genpod.rag import RagMember
from genpod.supervisor import SupervisorMember
from genpod.tests_generator import TestsGeneratorMember


class TeamMembers:
    """
    Manages a team of different agents.
    """
    def __init__(self, persistance_db_path: str, vector_db_collection: str) -> None:
        """
        Initializes the team members with their configurations and state/graph setups.
        """

        self.supervisor = SupervisorMember(persistance_db_path)
        self.supervisor.set_role_to_manager()

        self.architect = ArchitectMember(persistance_db_path)
        self.architect.set_role_to_lead()

        self.coder = CoderMember(persistance_db_path)
        self.coder.set_role_to_member()

        self.planner = PlannerMember(persistance_db_path)
        self.planner.set_role_to_member()

        self.rag = RagMember(persistance_db_path, vector_db_collection)
        self.rag.set_role_to_member()

        self.tests_generator = TestsGeneratorMember(persistance_db_path)
        self.tests_generator.set_role_to_member()
        
    def get_team_members_as_list(self) -> list[AgentMember]:
        """
        """

        members = []

        for attr_name in dir(self):

            attr_value = getattr(self, attr_name)

            if isinstance(attr_value, AgentMember):
                members.append(attr_value)

        return members

    def print_team(self) -> None:
        """
        Prints out the details of all team members.
        """
        import pprint as pp
        members = self.get_team_members_as_list()
        for member in members:
            print("\n")
            pp.pprint(str(member))
            print("\n")
