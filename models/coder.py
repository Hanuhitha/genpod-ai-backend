"""
This module defines the data model for the output of the Coder agent. 

The Coder agent is responsible for completing tasks in a project. The output of 
the Coder agent includes information about the steps to complete a task, 
the files to be created, the location of the code, the actual code.
"""
from typing import Any, Dict

from pydantic import BaseModel, Field
from typing_extensions import ClassVar


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


class CoderModel(BaseModel):
    """
    A data model representing the output of the Coder agent.

    This model includes various fields that capture the details of the task 
    completion process, such as the steps to complete the task, the files to
    be created, the location of the code, and the actual code.
    """
    can_complete_task: bool = Field(
        description="can task be completed?",
        required=True
    )

    task_abandon_remarks: str = Field(
        description="reason why task was abandoned.",
        required=True
    )

    is_add_info_needed: bool = Field(
        description="If you need additional ifnormation to complete a task or not.",
        required=True
    )

    question_for_additional_info: str = Field(
        description="what new information you need?"
    )

    files_to_create: str = Field(
        description="A list of absolute file paths that need to be created as part of the current task",
        required=True
    )

    code: str = Field(
        description="The complete, well-documented working code that adheres to all "
        "standards requested with the programming language, framework user requested ",
        required=True
    )

    infile_license_comments: dict[str, str] = Field(
        description="The multiline standard license comment which goes on top of each file."
        "key should be the extension of the file, ex: language: python, key: .py"
        "language: C++, key: .cpp, language: Markdown, key: .md, language: C#, key: .cs"
        "value of these any of these keys should be the license commented in multiline "
        "format.",
        required=True
    )

    tool_calls: list[ToolCall] = Field(
        description="List of tool calls that need to be made to complete the task",
        required=True
    )

    description: ClassVar[str] = "Schema representing the output from the "
    "Coder agent upon task completion."


class FileSetupPlan(BaseModel):
    """
    Represents the setup plan for files, including file creation details and terminal commands to be executed.
    """

    files_to_create: dict[str, str] = Field(
        description="""
        A dictionary where each key is an absolute file path and the corresponding
        value is a detailed description of the file. The description should specify
        what the file should contain or its purpose, providing enough information
        to understand its role in the project.

        Example:
            {
                '/absolute/path/to/file1.py': 'Main script for data processing. This file should include the core logic for processing data inputs and outputs.',
                '/absolute/path/to/file2.md': 'README file with project information. Include project overview, installation instructions, and usage examples.'
            }
        """,
        default={},
        title="Files to Create with Detailed Descriptions",
        example={
            '/home/user/project/main.py': 'Main script for data processing. This file should include the core logic for processing data inputs and outputs.',
            '/home/user/project/README.md': 'README file with project information. Include project overview, installation instructions, and usage examples.'
        }
    )

    terminal_commands: dict[str, Dict[str, Dict[str, str]]] = Field(
        description="""
        A dictionary where each key is an absolute file path, and each value is another dictionary
        specifying commands to be executed before or after the file creation. The inner dictionary has
        two keys: 'before' and 'after', each mapping to another dictionary. This nested dictionary maps
        each directory path where the command should be executed to the command itself. Commands must come
        from the approved list and should avoid restricted symbols like '&&', '||', '|', and ';'. The
        allowed commands are: 'docker', 'python', 'python3', 'pip', 'virtualenv', 'mv', 'pytest',
        'touch', and 'git'.

        Example:
            {
                '/absolute/path/to/file1.py': {
                    'before': {
                        '/home/user/project': 'mkdir new_directory',
                        '/home/user/project/scripts': 'python3 setup.py'
                    },
                    'after': {
                        '/home/user/project': 'echo "File creation completed"'
                    }
                },
                '/absolute/path/to/file2.md': {
                    'before': {
                        '/home/user/project': 'touch new_file.md'
                    },
                    'after': {}
                }
            }
        """,
        default={},
        title="Terminal Commands with Before and After Execution",
        example={
            '/home/user/project/main.py': {
                'before': {
                    '/home/user/project': 'mkdir new_directory',
                    '/home/user/project/scripts': 'python3 setup.py'
                },
                'after': {
                    '/home/user/project': 'echo "File creation completed"'
                }
            },
            '/home/user/project/README.md': {
                'before': {
                    '/home/user/project': 'touch new_file.md'
                },
                'after': {}
            }
        }
    )


class FileContent(BaseModel):
    """
    Represents the content plan for files, including the code to be included in each file and license comments.
    This simplified version assumes a single code snippet and license comment for all files.
    """

    file_code: str = Field(
        description="""
        The code content to be included in all files. This single string will be used as the content for each file.
        Ensure the code adheres to the required standards and includes necessary documentation.

        Example:
            'print("Hello, world!")'
        """,
        default='',
        title="File Code Content",
        example='print("Hello, World!")'
    )

    license_comments: Dict[str, str] = Field(
        description="""
        A dictionary where the key is the file extension (including the dot) and the value is the license comment
        to be added at the top of files with that extension. This allows for different comment formats for different
        types of files.

        Example:
            {
                ".py": "''' \nSPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of [Your Organization] & [Your Project]\n'''",
                ".md": "<!-- SPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of [Your Organization] & [Your Project] -->"
            }
        """,
        default={},
        title="License Comments by File Extension",
        example={
            ".py": "''' \nSPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of [Your Organization] & [Your Project]\n'''",
            ".md": "<!-- SPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of [Your Organization] & [Your Project] -->"
        }
    )


class CodeGenerationPlan(BaseModel):
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

    code: dict[str, str] = Field(
        description="""
        A dictionary where each key-value pair represents a file and its corresponding code. The key 
        should be the absolute path to the file, and the value should be the well-documented working 
        code for that particular file. The code should adhere to all the requirements and standards 
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
