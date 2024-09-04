from abc import ABC, abstractmethod

import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

from agents.agent.agent import Agent
from agents.supervisor.supervisor_state import SupervisorState
from configs.project_config import LLMConfig
from langchain.schema import HumanMessage, SystemMessage, FunctionMessage


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
        self.agents: Dict[str, Agent] = {}
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
        self.current_task = ""
        self.current_status = ""

        self.prompt_template = """

You are AgentMatcher, an intelligent assistant designed to analyze user queries and match them with
the most suitable agent or department. Your task is to understand the user's request,
identify key entities and intents, and determine which agent or department would be best equipped
to handle the query.

Important: The user's input may be a follow-up response to a previous interaction.
The conversation history, including the name of the previously selected agent, is provided.
If the user's input appears to be a continuation of the previous conversation
(e.g., "yes", "ok", "I want to know more", "1"), select the same agent as before.

Analyze the user's input and categorize it into one of the following agent types:
<agents>
{{AGENT_DESCRIPTIONS}}
</agents>
If you are unable to select an agent put "unkwnown"

Guidelines for classification:

    Agent Type: Choose the most appropriate agent type based on the nature of the query.
    For follow-up responses, use the same agent type as the previous interaction.
    Priority: Assign based on urgency and impact.
        High: Issues affecting service, billing problems, or urgent technical issues
        Medium: Non-urgent product inquiries, sales questions
        Low: General information requests, feedback
    Key Entities: Extract important nouns, product names, or specific issues mentioned.
    For follow-up responses, include relevant entities from the previous interaction if applicable.
    For follow-ups, relate the intent to the ongoing conversation.
    Confidence: Indicate how confident you are in the classification.
        High: Clear, straightforward requests or clear follow-ups
        Medium: Requests with some ambiguity but likely classification
        Low: Vague or multi-faceted requests that could fit multiple categories
    Is Followup: Indicate whether the input is a follow-up to a previous interaction.

Handle variations in user input, including different phrasings, synonyms,
and potential spelling errors.
For short responses like "yes", "ok", "I want to know more", or numerical answers,
treat them as follow-ups and maintain the previous agent selection.

Here is the conversation history that you need to take into account before answering:
<history>
{{HISTORY}}
</history>
If the message history have a hint of an agent used and the task finished, do not use the same agent again.

The general sequence of events is as follows:
Planner cannot function without input from Architect
Coder cannot function without input from Planner

Also refer to the current task information to choose what to do next. If the current status is awaiting, you might want to recall the same **agent**.
<current task and additional info>
{{CURRENT_TASK}}
{{CURRENT_STATUS}}

Examples:

1. Initial query with no context:
User: "What are the symptoms of the flu?"

userinput: What are the symptoms of the flu?
selected_agent: agent-name
confidence: 0.95

2. Context switching example between a TechAgentand a BillingAgent:
Previous conversation:
User: "How do I set up a wireless printer?"
Assistant: [agent-a]: To set up a wireless printer, follow these steps:
1. Ensure your printer is Wi-Fi capable.
2. Connect the printer to your Wi-Fi network.
3. Install the printer software on your computer.
4. Add the printer to your computer's list of available printers.
Do you need more detailed instructions for any of these steps?
User: "Actually, I need to know about my account balance"

userinput: Actually, I need to know about my account balance</userinput>
selected_agent: agent-name
confidence: 0.9

3. Follow-up query example for the same agent:
Previous conversation:
User: "What's the best way to lose weight?"
Assistant: [agent-name-1]: The best way to lose weight typically involves a combination
of a balanced diet and regular exercise.
It's important to create a calorie deficit while ensuring you're getting proper nutrition.
Would you like some specific tips on diet or exercise?
User: "Yes, please give me some diet tips"

userinput: Yes, please give me some diet tips
selected_agent: agent-name-1
confidence: 0.95

4. Multiple context switches with final follow-up:
Conversation history:
User: "How much does your premium plan cost?"
Assistant: [agent-name-a]: Our premium plan is priced at $49.99 per month.
This includes features such as unlimited storage, priority customer support,
and access to exclusive content. Would you like me to go over the benefits in more detail?
User: "No thanks. Can you tell me about your refund policy?"
Assistant: [agent-name-b]: Certainly! Our refund policy allows for a full refund within 30 days
of purchase if you're not satisfied with our service. After 30 days, refunds are prorated based
on the remaining time in your billing cycle. Is there a specific concern you have about our service?
User: "I'm having trouble accessing my account"
Assistant: [agenc-name-c]: I'm sorry to hear you're having trouble accessing your account.
Let's try to resolve this issue. Can you tell me what specific error message or problem
you're encountering when trying to log in?
User: "It says my password is incorrect, but I'm sure it's right"

userinput: It says my password is incorrect, but I'm sure it's right
selected_agent: agent-name-c
confidence: 0.9

Skip any preamble and provide only the response in the specified format.
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

    def set_current_task_and_status(self, task_info, current_status) -> None:
        self.current_task = self.format_messages([task_info])
        self.current_status = self.format_messages([current_status])

    @staticmethod
    def replace_placeholders(template: str, variables) -> str:
        return re.sub(r'{{(\w+)}}',
                      lambda m: '\n'.join(
                          variables.get(m.group(1), [m.group(0)]))
                      if isinstance(variables.get(m.group(1)), list)
                      else variables.get(m.group(1), m.group(0)), template)

    def update_system_prompt(self) -> None:
        all_variables = {
            "AGENT_DESCRIPTIONS": self.agent_descriptions,
            "HISTORY": self.history,
            "CURRENT_TASK": self.current_task,
            "CURRENT_STATUS": self.current_status
        }
        self.system_prompt = self.replace_placeholders(
            self.prompt_template, all_variables)

    def set_system_prompt(self,
                          template: Optional[str] = None,
                          variables: Optional[TemplateVariables] = None) -> None:
        if template:
            self.prompt_template = template
        if variables:
            self.custom_variables = variables
        self.update_system_prompt()

    @staticmethod
    def format_messages(messages: List[tuple]) -> str:
        return "\n".join([
            f"{message[0]}: {' '.join([message[1]])}" for message in messages
        ])


class SupervisorClassifier(Classifier):
    def __init__(self, llm: ChatOpenAI) -> None:
        super().__init__()
        self.llm = llm
        self.llm = self.llm.bind_tools(self.tools)

    def set_agents(self, team) -> None:
        agents = {x.member_id: x for x in team.get_team_members_as_list(
        ) if 'super' not in x.member_name.lower()}

        self.agent_descriptions = "\n\n".join(f"{agent.member_id}:{agent.description}"
                                              for agent in agents.values())
        self.agents = agents

    def process_request(self,
                        state: SupervisorState):

        user_input = state['original_user_input']
        messages = [

            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=user_input),
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
        self.set_current_task_and_status(state['current_task'].description, state['current_task'].task_status.value

                                         )
        self.update_system_prompt()
        return self.process_request(state)
