"""
"""

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.skeleton import FunctionSkeleton
from models.tests_generator import TestCodeGeneration


class TestGeneratorPrompts:

    test_generation_prompt: PromptTemplate =PromptTemplate(
        template="""
        As an expert programmer specialized in Unit test case generation, generate unit test case for the tasks that have functionality which requires unit test cases. In a test driven development you play a crucial role in creating the unit test cases first using which user will create their functionality to abide by the test cases. You are collaborating with a team to complete an end-to-end project 
        requested by a user. You should generate the unit test cases using the functions skeletons that are provided 

        You are currently working on the following project:
        Project Name: '{project_name}'

        Project Path: '{project_path}'

        From document provided below you will find facts about the project and set of guidelines to be 
        followed while developing the project. Please adhere to the following guidelines specified by 
        your team lead:
        "{requirements_document}"

        The project requires certain files and directories. The required folder structure for the 
        project is as follows at path:
        "{folder_structure}"
        

        The function skeletons in a given file 

        Error messages will only be present if there is an issue with your previous response. 
        "{error_message}"

        The instructions for formatting are as follows:
        {format_instructions}

        Format the files to be created as a list of strings. For example:
        "[file_path1, file_path2, file_path3, ..., file_pathN]"

        To complete each task, you should select at least one tool. The tools should be executed in 
        the order they are listed.

        Now, here is your task to complete.
        {task}.

        These are the functions skeletons dictionary the key contains the path where the functions are supposed to be created and value contains the function skeleton with function name, input parameters, return type and function description for which you need to create unit test cases 
        "{functions_skeleton}"
        """,
        input_variables=['project_name', 'project_path', 'requirements_document', 'folder_structure', 'error_message', 'task' , 'functions_skeleton'],
        partial_variables= {
            "format_instructions": PydanticOutputParser(pydantic_object=TestCodeGeneration).get_format_instructions()
        }
    )
    
    skeleton_generation_prompt: PromptTemplate = PromptTemplate(
        template="""
        You are a highly skilled software developer assistant. Your task is to generate a detailed function skeleton based on the provided description.


        You are currently working on the following project:
        Project Name: '{project_name}'

        Project Path: '{project_path}'

        From document provided below you will find facts about the project and set of guidelines to be 
        followed while developing the project. Please adhere to the following guidelines specified by 
        your team lead:
        "{requirements_document}"

        The project requires certain files and directories. The required folder structure for the 
        project is as follows at path:
        "{folder_structure}"

        Error messages will only be present if there is an issue with your previous response. 
        "{error_message}"

        The instructions for formatting are as follows:
        {format_instructions}

        Please ensure that the function description is clear and detailed, specifying the exact steps or logic that need to be implemented within the function. 

        Format the files to be created as a list of strings. For example:
        "[file_path1, file_path2, file_path3, ..., file_pathN]"

        To complete each task, you should select at least one tool. The tools should be executed in 
        the order they are listed.

        Now, here is your task to complete.
        {task}.
        """,
        input_variables=['project_name', 'project_path', 'requirements_document', 'folder_structure', 'error_message', 'task' ],
        partial_variables= {
            "format_instructions": PydanticOutputParser(pydantic_object=FunctionSkeleton).get_format_instructions()
        }
    )
