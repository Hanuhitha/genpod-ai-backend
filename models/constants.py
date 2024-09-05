"""
This `enums.py` module contains various enumerations used throughout the project. 
These enumerations provide a systematic way to represent distinct values and 
categories using symbolic names, enhancing the readability and maintainability 
of the code. Each enumeration is defined as a separate class and can be imported 
for use in other modules.
"""
from enum import Enum


class ChatRoles(Enum):
    """
    An enumeration representing the various roles in a chat conversation with 
    the Language Learning Model (LLM) using the ChatPromptTemplate.

    This class is used to categorize the messages in the graph state according 
    to the role of the sender. The roles include 'assistant' (AI), 'tool', 
    'user', and 'system'. These roles help in identifying who sent a particular 
    message or performed a certain action in the conversation.

    Attributes:
        AI (str): Represents the assistant's role in the conversation.
        TOOL (str): Represents the tool's role in the conversation.
        USER (str): Represents the user's role in the conversation.
        SYSTEM (str): Represents the system's role in the conversation.
    """

    AI: str = "assistant"
    TOOL: str = "tool"
    USER: str = "user"
    SYSTEM: str = "system"

    def __str__(self):
      """
      Returns the string representation of the Enum member.

      Returns:
          str: The value of the Enum member.
      """
      return self.value
    
class Status(Enum):
    """
    An enumeration representing the various states a task or project can be in.

    This class is used to track the progress of a task or project. The states 
    include 'NEW', 'AWAITING', 'INPROGRESS', 'ABANDONED', and 'DONE'. These 
    states help in identifying the current status of a task or project.

    Attributes:
        NONE (str): Represents the task is empty.
        NEW (str): Represents the initial state of a task or project.
        AWAITING (str): Represents the state when a task or project is waiting
          for some event or dependency.
        RESPONDED (str): Indicates that the task or project was previously in 
          the 'AWAITING' state and has now received the necessary response.
        INPROGRESS (str): Represents the state when a task or project is 
          currently being worked on.
        ABANDONED (str): Represents the state when a task or project has been 
          left incomplete.
        DONE (str): Represents the state when a task or project has been 
          completed.
    """
    NONE: str = "NONE"
    NEW: str = "NEW"
    AWAITING: str = "AWAITING"
    RESPONDED: str = "RESPONDED"
    INPROGRESS: str = "INPROGRESS"
    ABANDONED: str = "ABANDONED"
    DONE: str = "DONE"

    def __str__(self):
      """
      Returns the string representation of the Enum member.

      Returns:
          str: The value of the Enum member.
      """
      return self.value

class PStatus(Enum):
    """
    An enumeration representing the various states a project can be in.

    This class is used to track the progress of a project. The states
    include 'RECEIVED', 'NEW', 'INITIAL', 'EXECUTING', 'MONITORING', 
    'HALTED', and 'DONE'. These states help in identifying the current 
    status of a project or task.

    Attributes:
        NONE (str): Initial state indicating no status has been assigned yet.
        RECEIVED (str): Indicates that the project has been received but has 
          not yet been assigned a specific status.
        NEW (str): Represents the pre-initiation state of a project.
        INITIAL (str): Represents the initial state when a project is waiting 
          for setup to be completed.
        EXECUTING (str): Represents the state of the project when a task is 
          currently being worked on.
        MONITORING (str): Represents the state of the project when issues 
          have arisen during task execution.
        HALTED (str): Represents the state when all tasks have been completed 
          or when an unresolved issue requires human intervention.
        DONE (str): Represents the state when all user-requested requirements 
          have been fulfilled.
    """

    NONE: str = "NONE"
    RECEIVED: str = "RECEIVED"
    NEW: str = "NEW"
    INITIAL: str = "INITIAL"
    EXECUTING: str = "EXECUTING"
    MONITORING: str = "MONITORING"
    HALTED: str = "HALTED"
    DONE: str = "DONE"

    def __str__(self):
      """
      Returns the string representation of the Enum member.

      Returns:
          str: The value of the Enum member.
      """
      return self.value
