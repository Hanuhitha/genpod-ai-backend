"""
This module defines the data model for the output of the Coder agent. 

The Coder agent is responsible for completing tasks in a project. The output of 
the Coder agent includes information about the steps to complete a task, 
the files to be created, the location of the code, the actual code.
"""
import re

from typing import Any, Dict

from pydantic import BaseModel, Field, model_validator
from configs.shell_config import CODER_COMMANDS

class FileContent(BaseModel):
    """
    Represents the content plan for files, including the code to be included in each file and license comments.
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

    @model_validator(mode="before")
    def check_field__file_code(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        file_code = values.get('file_code')

        if not file_code:
            raise ValueError('file_code cannot be an empty string.')
        
        if not isinstance(file_code, str):
            raise ValueError('file_code must be a string.')
        
        return values
    
    @model_validator(mode='before')
    def check_field__license_comments(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        license_comments = values.get('license_comments')

        if not isinstance(license_comments, dict):
            raise ValueError('license_comments must be a dictionary.')
        
        for key, value in license_comments.items():
            if not isinstance(key, str) or not key.startswith('.'):
                raise ValueError(f'Invalid file extension key: {key}. Must be a string starting with a dot.')
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'License comment for extension "{key}" must be a non-empty string.')
            
        return values

# TODO: Temporarily disable certain conditional checks to enhance application performance.
# During testing, these checks caused the log file size to increase from 150MB to 550MB,
# and significantly extended project generation time to 4 hours.
# Revisit and optimize these checks for a balance between performance and logging.
class CodeGenerationPlan(BaseModel):
    """
    Represents a plan for generating files with specified content and terminal commands
    """

    file: Dict[str, FileContent] = Field(
        description="""
        A dictionary where each key is a file path and each value is the content plan for that file.
        The content plan includes the code to be included in the file and license comments based on the file extension.

        Example:
            {
                '/path/to/file1.py': {
                    'file_code': 'print("Hello, World!")',
                    'license_comments': {
                        '.py': "''' \nSPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of [Your Organization] & [Your Project]\n'''"
                    }
                },
                '/path/to/file2.md': {
                    'file_code': '# Markdown content',
                    'license_comments': {
                        '.md': "<!-- SPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of [Your Organization] & [Your Project] -->"
                    }
                }
            }
        """,
        default={},
        title="File Content Plans",
        example={
            '/home/user/project/main.py': {
                'file_code': 'print("Hello, World!")',
                'license_comments': {
                    '.py': "''' \nSPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of [Your Organization] & [Your Project]\n'''"
                }
            },
            '/home/user/project/README.md': {
                'file_code': '# Markdown content',
                'license_comments': {
                    '.md': "<!-- SPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of [Your Organization] & [Your Project] -->"
                }
            }
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

    @model_validator(mode='before')
    def check_field__file(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        file = values.get('file')

        if not file:
            raise ValueError('file cannot be an empty.')
        
        if not isinstance(file, dict):
            raise ValueError('The "file" field must be a dictionary.')
        
        for path, content in file.items():
            if not isinstance(path, str) or not path:
                raise ValueError(f'File path "{path}" must be a non-empty string.')
            
            if not isinstance(content, dict):
                raise ValueError(f'Content for "{path}" must be a valid FileContent instance.')
        
            try:
                FileContent(**content)
            except ValueError as e:
                raise ValueError(f'Invalid content for file "{path}": {e}')
            
        return values
    
    @model_validator(mode='before')
    def check_field__terminal_commands(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        allowed_commands = CODER_COMMANDS
        restricted_symbols = re.compile(r'[&|;]')
        
        terminal_commands = values.get('terminal_commands')
        # if not terminal_commands:
        #     raise ValueError('terminal_commands cannot be an empty.')
        
        if not isinstance(terminal_commands, dict):
            raise ValueError('The "terminal_commands" field must be a dictionary.')
        
        for path, actions in terminal_commands.items():
            if not isinstance(path, str) or not path:
                raise ValueError(f'Terminal command path "{path}" must be a non-empty string.')
            if not isinstance(actions, dict) or 'before' not in actions or 'after' not in actions:
                raise ValueError(f'Terminal command actions for "{path}" must be a dictionary with "before" and "after" keys.')
            
            for phase in ['before', 'after']:
                for dir_path, command in actions[phase].items():
                    if not isinstance(dir_path, str) or not dir_path:
                        raise ValueError(f'Directory path "{dir_path}" for command in phase "{phase}" must be a non-empty string.')
                    # if not isinstance(command, str) or restricted_symbols.search(command):
                    #     raise ValueError(f'Command "{command}" in phase "{phase}" contains restricted symbols.')
                    # TODO: Disabling this logic just for now. Need to figure out how to handle in case of raising this exception.
                    # if not any(cmd in command for cmd in allowed_commands):
                    #     raise ValueError(f'Command "{command}" in phase "{phase}" is not an approved command.')
        
        return values
