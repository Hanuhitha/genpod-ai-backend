from abc import ABC, abstractmethod

import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

from agents.agent.agent import Agent
from agents.supervisor.supervisor_state import SupervisorState
from configs.project_config import LLMConfig
from langchain.schema import HumanMessage, SystemMessage, FunctionMessage
from prompts.supervisor_prompts import SupervisorPrompts

TemplateVariables = Dict[str, Union[str, List[str]]]


@dataclass
class ClassifierResult:
    selected_agent: Optional[Agent]
    confidence: float
    reason: str


class Classifier(ABC):
    def __init__(self):
        # self.default_agent =  should go to supervisor agent

        self.agent_descriptions = ""
        self.history = ""
        self.system_prompt = ""
        self.user_input = ''
        self.agents: Dict[str, Agent] = {}
        self.visited_agents = []
        self.project_status = ''
        self.tools = [
            {
                "name": "analyzePrompt",
                "description": "Analyze the process flow input and provide structured output. Selected agent cannot be None",

                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_flow": {
                            "type": "string",
                            "description": "The process flow, flags and status"
                        },
                        "selected_agent": {
                            "type": "string",
                            "description": "The name of the selected agent. Selected agent cannot be None."
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence level between 0 and 1"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the selected agent"
                        },

                    },
                    "required": ["selected_agent", "confidence", 'reason'],

                }

            }
        ]
        self.current_agent = ""
        self.current_status = ""
        self.flags = ""

        self.project_flow = """
        **Genpod Development Team Workflow:**
        The workflow begins when the user provides the initial input. Based on the *project status* flag, different team members take on specific roles and responsibilities.
        1. **When Project Status is 'NEW':**   
        If the *project status* is set to 'NEW', the RAG agent must gather additional information required for further processing. This stage is crucial to ensure that all necessary data is collected before moving forward.
        2. **When Project Status is 'INITIAL':**  
        If the *project status* is 'INITIAL', the Architect agent is responsible for preparing the requirements document, which defines the scope and serves as the blueprint for the next phases.
        3. **When Project Status is 'Monitoring':**  
        If the *project status* is 'Monitoring' and the task status is 'AWAITING', and the request was initiated by the Architect (calling agent), the RAG agent must provide the necessary information. If the RAG agent cannot provide this information, it should be gathered from a human resource.
        4. **When Project Status is 'Executing':**  
        - If  *are_planned_tasks_in_progress* is False, the Planner is responsible for preparing them.  
        - If planned tasks is True, the Coder and Tester must complete them.
        5. **Special Considerations in the 'Executing' Status:**  
        - If the task status is 'DONE' or 'ABANDONED', the Supervisor can assign new tasks for the Planner.  
        - If the task status is 'IN PROGRESS', the Coder and Tester are responsible for completing the available tasks.  
        - If *is_function_generation_required* is True, the Tester must first complete the unit test cases, after which the Coder can finish the task. 
        - Invoking call_test_code_generator due to Project Status is 'Executing' and Planned Task involving is_function_generation_required and is_test_code_generated.
        - If function generation is not required and in the Planned Task  *is_code_generate* is False and PlannedTask Status is 'NEW',the Coder can complete the task independently. 
        6. **When Project Status is 'DONE':**  
        When the *project status* is set to 'DONE',the system should trigger an automatic update to reflect the completion of all tasks.
         """

    def set_agents(self, agents: Dict[str, Agent]) -> None:
        self.agent_descriptions = "\n\n".join(f"{agent.agent_id}:{agent.description}"
                                              for agent in agents.values())
        self.agents = agents

    def get_all_agents(self) -> Dict[str, Dict[str, str]]:
        return {key: {
            "name": agent.agent_name,
            "description": agent.description
        } for key, agent in self.agents.items()}

    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        if not agent_id:
            return None
        return self.agents.get(agent_id)

    def set_history(self, messages) -> None:
        self.history = self.format_messages(messages)

    def set_additional_info(self, state) -> None:
        flags = []
        self.current_agent = state['current_agent']
        self.current_status = state['current_task'].task_status.value
        self.visited_agents = state['visited_agents']
        self.project_status = state['project_status'].value
        if "current_planned_task" in state:
            flags.append(
                f"is_function_generation_required : {state['current_planned_task'].is_function_generation_required}")
        if "current_planned_task" in state:
            flags.append(
                f"is_test_code_generated : {state['current_planned_task'].is_test_code_generated}")
            flags.append(
                f"is_code_generate : {state['current_planned_task'].is_code_generate}")
        if "are_planned_tasks_in_progress" in state:
            flags.append(
                f"are_planned_tasks_in_progress : {state['are_planned_tasks_in_progress']}")
        self.flags = "\n".join(flags)

    @staticmethod
    def replace_placeholders(template: str, variables) -> str:
        return template.format(**variables)
        # return re.sub(r'{{(\w+)}}',
        #               lambda m: '\n'.join(
        #                   variables.get(m.group(1), [m.group(0)]))
        #               if isinstance(variables.get(m.group(1)), list)
        #               else variables.get(m.group(1), m.group(0)), template)

    def update_system_prompt(self) -> None:
        all_variables = {
            "agent_descriptions": self.agent_descriptions,
            "history": self.history,
            "current_agent": self.current_agent,
            "current_status": self.current_status,
            "user_prompt": self.user_input,
            "visited_agents": self.visited_agents,
            "project_status": self.project_status,
            "project_flow": self.project_flow,
            "flags": self.flags
        }
        self.system_prompt = self.replace_placeholders(
            self.prompt_template, all_variables)

    # def set_system_prompt(self,
    #                       template: Optional[str] = None,
    #                       variables: Optional[TemplateVariables] = None) -> None:
    #     if template:
    #         self.prompt_template = template
    #     if variables:
    #         self.custom_variables = variables
    #     self.update_system_prompt()

    @staticmethod
    def format_messages(messages: List[tuple]) -> str:
        return "\n".join([
            f"{message[0]}: {' '.join([message[1]])}" for message in messages
        ]) if len(messages) > 0 else ""


class SupervisorClassifier(Classifier, SupervisorPrompts):
    def __init__(self, llm: ChatOpenAI) -> None:
        super().__init__()
        self.llm = llm
        self.llm = self.llm.bind_tools(self.tools)
        self.prompt_template = self.classifier_prompt

    def set_agents(self, team) -> None:
        agents = {x.member_id: x for x in team.get_team_members_as_list(
        )}

        self.agent_descriptions = "\n\n".join(f"{agent.member_id}:{agent.description}"
                                              for agent in agents.values())
        self.agents = agents

    def process_request(self,
                        state: SupervisorState):

        self.user_input = state['original_user_input']
        self.update_system_prompt()
        messages = [

            SystemMessage(content="You are a helpful assistant."),
            SystemMessage(
                content=self.system_prompt)

        ]

        response = self.llm.invoke(messages)
        selected_agent = response.tool_calls[0]['args']['selected_agent']
        selected_conf = response.tool_calls[0]['args']['confidence']
        reason = response.tool_calls[0]['args']['reason']

        intent_classifier_result = ClassifierResult(
            selected_agent=self.get_agent_by_id(selected_agent),
            confidence=float(selected_conf),
            reason=reason
        )
        print(intent_classifier_result)
        return intent_classifier_result

    def classify(self, state: SupervisorState) -> ClassifierResult:
        chat_history = state['messages'][-15:]
        self.set_history(chat_history)
        self.set_additional_info(state)

        return self.process_request(state)
