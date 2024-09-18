"""
This module defines the data model for the output of the TestGenerator agent. 

The TestGenerator agent is responsible for completing tasks in a project. The output of 
the TestGenerator agent includes information about the steps to complete a task, 
the files to be created, the location of the code, the actual code.
"""

from typing import Any

from pydantic import BaseModel, Field


class FunctionSkeletonFields(BaseModel):
    """
    """
    
    function_name: str= Field(
        description="""
        A concise and descriptive name for the function.""", required=True
    )

    input_params: list[str] =Field(
        description="""
        A list of input parameters the function will take, including their types and descriptions""", required=True
    )

    return_type: list[str] = Field(
        description="""
        A description of the function's output, including its type and what it represents""",required=True 
    )

    function_description: str = Field(
        description="""
        A comprehensive description of what the function needs to do and how it should achieve its goal.""", required=True
    )

class FunctionSkeleton(BaseModel):
    """
    """
    skeletons_to_create: dict[str, FunctionSkeletonFields] = Field(
        description="""
        A dictionary where each key-value pair represents a file and its corresponding function skeleton. The key 
        should be the absolute path to the file, and the value should be the well-descriptive function skeleton
        for that particular file.
        """, 
        required=True
    )

class ToolCall(BaseModel):
    """
    """
    name: str = Field(
        description="The name of the tool to use", 
        required=True
    )

    args: dict[str, str] = Field(
        description="arguments to the tools",
        required=True
    )

class TestCodeGeneration(BaseModel):
    """
    """

    files_to_create: list[str] = Field(
        description="""
        A list of absolute file paths that need to be created as part of the current task
        "
        [
            'absolute_file_path1', 
            'absolute_file_path2', 
            'absolute_file_path3',
            .
            .
            .
            .,
            'absolute_file_pathN'
        ]        
        """, 
        default=[],
        required=True
    )

    test_code: dict[str, str] = Field(
        description="""
        A dictionary where each key-value pair represents a file and its corresponding code. The key 
        should be the absolute path to the file, and the value should be the well-documented working 
        unit test code for that particular file. The code should adhere to all the requirements and standards 
        provided.
        """, 
        default={},
        required=True
    )

    infile_license_comments: dict[str, str] = Field(
        description="""
        The standard license text multiline comment which goes on top of each file, key of the dict 
        should be the extension of the file. 
        "
            {
                ".py": "multiline commment",
                ".md": "multiline comment",
                ".yml": "multiline comment",
            }
        "
        """,
        default={},
        required=True
    )

    commands_to_execute: dict[str, str] = Field(
        description="""
        This field represents a dictionary of commands intended to be executed on a Linux terminal. Each key-value pair in the dictionary corresponds to an absolute path (the key) and a specific command (the value) to be executed at that path.

        Please adhere to the following guidelines while populating this field:
        - The key should be the absolute path where the command is to be run.
        - Only commands from the approved list are allowed. The approved commands include 'mkdir', 'docker', 'python', 'python3', 'pip', 'virtualenv', 'mv', 'pytest', and 'touch', 'git'.
        - For security reasons, the use of certain symbols is restricted. Specifically, the following symbols are not permitted: '&&', '||', '|', ';'.

        Please ensure that the commands and their parameters are correctly formatted to prevent any execution errors.
        """,
        default={},
        required=True
    )

    functions_skeleton: dict[str, FunctionSkeletonFields] = Field(
        description="""
        A dictionary where each key-value pair represents a file and its corresponding function skeleton. The key 
        should be the absolute path to the file, and the value should be the well-descriptive function skeleton
        for that particular file.
        """, 
        default={},
        required=True
    )

    def __getitem__(self, key: str) -> Any:
        """
        Allows getting attributes using square bracket notation.
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Key '{key}' not found in TestCodeGeneration.")

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Allows setting attributes using square bracket notation.
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Key '{key}' not found in TestCodeGeneration.")
