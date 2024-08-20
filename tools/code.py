"""
This module provides a FS class with a method to write generated code to a specified file.
"""
import codecs
import os
from typing import Annotated

from langchain.tools import tool


class CodeFileWriter:
    """
    This class provides a method to write generated code to a specified file.
    """
    
    @tool
    def write_generated_code_to_file(
        generated_code: Annotated[
            str, 
            "The string of code that was generated by the agent. This code will be written to a file."
        ],
        file_path: Annotated[
            str, 
            "The absolute path, including the filename and extension, where the generated code will be written. If the directory does not exist, it will be created."
        ]
    ) -> tuple[bool, str]:
        """
        Writes the provided generated code to the specified file.

        Args:
            generated_code (str): The string of code that was generated by the agent. 
            This code will be written to a file.
            file_path (str): The absolute path, including the filename and extension, 
            where the generated code will be written. If the directory does not exist, 
            it will be created.

        Returns:
            tuple: A tuple containing a boolean and a string. The boolean indicates 
            whether an error occurred (True if an error occurred, False otherwise). 
            The string provides a detailed message, either indicating the successful 
            writing of the generated code to the specified file or describing the 
            error that occurred.
        """

        try:
            # Ensure the directory exists before writing the file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            try:
                with codecs.open(file_path, 'w', encoding='utf-8') as file:
                    file.write(generated_code)
            except UnicodeEncodeError:
                # If UTF-8 fails, try with 'utf-8-sig' (UTF-8 with BOM)
                with codecs.open(file_path, 'w', encoding='utf-8-sig') as file:
                    file.write(generated_code)
                    
            return (False, f"Success! The generated code was written to the following location: '{file_path}'.")
        except BaseException as e:
            return (True, f"An error occurred while attempting to write the generated code to the file. Here's what went wrong: '{repr(e)}'.")
        
    @tool
    def write_generated_skeleton_to_file(
        generated_code: Annotated[
            str, 
            "The string of code that was generated by the agent. This code will be written to a file."
        ],
        file_path: Annotated[
            str, 
            "The absolute path, including the filename and extension, where the generated code will be written. If the directory does not exist, it will be created."
        ],
        generated_project_path : Annotated[str, """The project path"""]
    ) -> tuple[bool, str]:
        """
        Writes the provided generated code to the specified file.

        Args:
            generated_code (str): The string of code that was generated by the agent. 
            This code will be written to a file.
            file_path (str): The absolute path, including the filename and extension, 
            where the generated code will be written. If the directory does not exist, 
            it will be created.

        Returns:
            tuple: A tuple containing a boolean and a string. The boolean indicates 
            whether an error occurred (True if an error occurred, False otherwise). 
            The string provides a detailed message, either indicating the successful 
            writing of the generated code to the specified file or describing the 
            error that occurred.
        """

        try:
            path_creation= file_path.split(generated_project_path)
            file_path=generated_project_path + '/docs/skeleton'+path_creation[1]
            # Ensure the directory exists before writing the file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            try:
                with codecs.open(file_path, 'w', encoding='utf-8') as file:
                    file.write(generated_code)
            except UnicodeEncodeError:
                # If UTF-8 fails, try with 'utf-8-sig' (UTF-8 with BOM)
                with codecs.open(file_path, 'w', encoding='utf-8-sig') as file:
                    file.write(generated_code)
                    
            return (False, f"Success! The generated code was written to the following location: '{file_path}'.")
        except BaseException as e:
            return (True, f"An error occurred while attempting to write the generated code to the file. Here's what went wrong: '{repr(e)}'.")
        