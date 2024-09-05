from abc import ABC, abstractmethod

import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

from agents.agent.agent import Agent
from agents.supervisor.supervisor_state import SupervisorState
from configs.project_config import LLMConfig
from langchain.schema import HumanMessage, SystemMessage, FunctionMessage
from prompts.supervisor import SupervisorPrompts

TemplateVariables = Dict[str, Union[str, List[str]]]


@dataclass
class ClassifierResult:
    selected_agent: Optional[Agent]
    confidence: float


class Classifier(ABC):
    def __init__(self):
        # self.default_agent =  should go to supervisor agent

        self.agent_descriptions = ""
        self.history = ""
        self.system_prompt = ""
        self.user_input = ''
        self.agents: Dict[str, Agent] = {}
        self.visited_agents = []
        self.tools = [
            {
                "name": "analyzePrompt",
                "description": "Analyze the user input and provide structured output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "userinput": {
                            "type": "string",
                            "description": "The original user input"
                        },
                        "selected_agent": {
                            "type": "string",
                            "description": "The name of the selected agent"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence level between 0 and 1"
                        }
                    },
                    "required": ["userinput", "selected_agent", "confidence"]
                }
            }
        ]
        self.current_agent = ""
        self.current_status = ""

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

    def set_additional_info(self, task_info, current_status, visited_agents) -> None:
        self.current_agent = self.format_messages([task_info])
        self.current_status = self.format_messages([current_status])
        self.visited_agents = self.format_messages(visited_agents)

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
            "visited_agents": self.visited_agents
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

        intent_classifier_result = ClassifierResult(
            selected_agent=self.get_agent_by_id(selected_agent),
            confidence=float(selected_conf)
        )
        print(intent_classifier_result)
        return intent_classifier_result

    def classify(self, state: SupervisorState) -> ClassifierResult:
        chat_history = state['messages']
        self.set_history(chat_history)
        self.set_additional_info(state['current_agent'], state['current_task'].task_status.value,
                                 state['visited_agents'])

        return self.process_request(state)
