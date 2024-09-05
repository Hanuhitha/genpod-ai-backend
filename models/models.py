"""
This module, `models.py`, contains various data models used throughout the project.

Each class in this module represents a different data model, with each model 
capturing a specific set of information required for the project. These models
are used to structure the data in a consistent and organized manner, enhancing 
the readability and maintainability of the code.
"""
from typing import Any, List

from pydantic import BaseModel, Field

from models.constants import Status
from utils.task_utils import generate_task_id


class Task(BaseModel):
    """
    A data model representing a task and its current state within a project
    or workflow.
    """
    task_id: str = Field(
        description="A unique task id to track and access current task and previous tasks",
        default_factory=generate_task_id
    )

    task_status: Status = Field(
        description="The current status indicating the progress of the task",
        default= Status.NONE,
        required=True
    )

    description: str = Field(
        description="A brief description outlining the objective of the task",
        default="",
        required=True
    )

    additional_info: str = Field(
        description="Additional info requested.",
        default=""
    )

    question: str = Field(
        description="Question to supervisor if additional information is needed"
        " to proceed with task execution.",
        default=""
    )

    remarks: str = Field(
        description="A field for notes on the task's status. If the task is "
        "abandoned, state the reason here.",
        default=""
    )

class PlannedTask(BaseModel):
    """
    A data model representing a task and its current state within a project
    or workflow.
    """
    task_id: str = Field(
        description="A unique task id to track and access current task and previous tasks",
        default_factory=generate_task_id
    )

    task_status: Status = Field(
        description="The current status indicating the progress of the task",
        default= Status.NONE,
        required=True
    )

    # if this is True then test code has to be generated first
    # then code has to be generated.
    is_function_generation_required: bool = Field(
        description="whether the current task involves writing code.",
        default=False,
        required=True
    )

    is_test_code_generated: bool = Field(
        description="unit test cases generated or not for this task",
        default=False,
    )

    is_code_generate: bool = Field(
        description="funtional code is generated or not",
        default=False
    )

    description: str = Field(
        description="A brief description outlining the objective of the task",
        default="",
        required=True
    )

class RequirementsDocument(BaseModel):
    """
    This class encapsulates the various requirements of a project. 
    """

    project_overview: str = Field(
        description="A brief overview of the project.",
        default=""
    )
    
    project_architecture: str = Field(
        description="Detailed information about the project's architecture.",
        default=""
    )

    directory_structure: str = Field(
        description="A description of the project's directory and folder structure.",
        default=""
    )

    microservices_architecture: str = Field(
        description="Details about the design and architecture of the project's microservices.",
        default=""
    )

    tasks_overview: str = Field(
        description="An overview of the tasks involved in the project.",
        default=""
    )

    coding_standards: str = Field(
        description="The coding standards and conventions followed in the project.",
        default=""
    )

    implementation_process: str = Field(
        description="A detailed description of the implementation process.",
        default=""
    )

    project_license_information: str = Field(
        description="Information about the project's licensing terms and conditions.",
        default=""
    )

    def to_markdown(self) -> str:
        """
        Generates a Markdown-formatted requirements document for the project.

        Returns:
            str: A Markdown string representing the requirements document.
        """

        return f"""
# Project Requirements Document

## Project Overview
{self.project_overview}

## Project Architecture
{self.project_architecture}

## Directory Structure
{self.directory_structure}

## Microservices Architecture
{self.microservices_architecture}

## Tasks Overview
{self.tasks_overview}

## Coding Standards
{self.coding_standards}

## Implementation Process
{self.implementation_process}

## Project License Information
{self.project_license_information}
        """
    
    def __getitem__(self, key: str) -> Any:
        """
        Allows getting attributes using square bracket notation.
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Key '{key}' not found in RequirementsDocument.")

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Allows setting attributes using square bracket notation.
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Key '{key}' not found in RequirementsDocument.")

class TaskQueue(BaseModel):
    """
    A class to manage a queue of tasks with an index to keep track of the next task to process.
    """
    
    next: int = Field(
        description="index of next field",
        default=0
    )

    queue: List[Task] = Field(
        description="list of tasks",
        default=[]
    )

    def add_task(self, t: Task) -> None:
        """
        Adds a new task to the end of the queue.
        
        Args:
            t (Task): The Task object to be added.
        """
        self.queue.append(t)

    def add_tasks(self, tasks: List[Task]) -> None:
        """
        Adds a list of tasks to the end of the queue.
        
        Args:
            tasks (List[Task]): A list of Task objects to be added.
        """
        self.queue.extend(tasks)

    def get_next_task(self) -> Task:
        """
        Retrieves and advances to the next task in the queue.
        
        Returns:
            Task: The next Task object, or None if no tasks are left.
        """
        if self.next < len(self.queue):
            task = self.queue[self.next]
            self.next += 1
            return task
        return None

    def update_task(self, updated_task: Task) -> None:
        """
        Updates an existing task in the queue with the new values from the updated_task.

        Args:
            updated_task (Task): The updated Task object with new values.
        
        Raises:
            ValueError: If the task to be updated is not found in the queue.
        """
        for i, task in enumerate(self.queue):
            if task.task_id == updated_task.task_id:
                self.queue[i] = updated_task
                return
        raise ValueError(f"Task with ID {updated_task.task_id} not found in the queue.")

    def __str__(self) -> str:
        """
        Returns a string representation of the TaskQueue.
        
        Returns:
            str: A string representing the current tasks and the index of the next task.
        """
        return f"Tasks: {self.queue}, Next Index: {self.next}"

class PlannedTaskQueue(BaseModel):
    """
    A class to manage a queue of tasks with an index to keep track of the next task to process.
    """
    
    next: int = Field(
        description="index of next field",
        default=0
    )

    queue: List[PlannedTask] = Field(
        description="list of planned tasks",
        default=[]
    )

    def add_task(self, t: PlannedTask) -> None:
        """
        Adds a new task to the end of the queue.
        
        Args:
            t (Task): The Task object to be added.
        """
        self.queue.append(t)

    def add_tasks(self, tasks: List[PlannedTask]) -> None:
        """
        Adds a list of tasks to the end of the queue.
        
        Args:
            tasks (List[Task]): A list of Task objects to be added.
        """
        self.queue.extend(tasks)

    def get_next_task(self) -> PlannedTask:
        """
        Retrieves and advances to the next task in the queue.
        
        Returns:
            Task: The next Task object, or None if no tasks are left.
        """
        if self.next < len(self.queue):
            task = self.queue[self.next]
            self.next += 1
            return task
        return None

    def update_task(self, updated_task: PlannedTask) -> None:
        """
        Updates an existing task in the queue with the new values from the updated_task.

        Args:
            updated_task (Task): The updated Task object with new values.
        
        Raises:
            ValueError: If the task to be updated is not found in the queue.
        """
        for i, task in enumerate(self.queue):
            if task.task_id == updated_task.task_id:
                self.queue[i] = updated_task
                return
        raise ValueError(f"Task with ID {updated_task.task_id} not found in the queue.")

    def __str__(self) -> str:
        """
        Returns a string representation of the TaskQueue.
        
        Returns:
            str: A string representing the current tasks and the index of the next task.
        """
        return f"Tasks: {self.queue}, Next Index: {self.next}"
