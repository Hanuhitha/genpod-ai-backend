"""
"""
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.coder_models import CodeGenerationPlan


class CoderPrompts:

    code_generation_prompt: PromptTemplate = PromptTemplate(
        template="""
        As a skilled programmer, you are an integral part of a team effort to deliver a comprehensive end-to-end 
        project as per the user's request. Your expertise is in developing well-documented, optimized, secure, and 
        production-ready code. Please focus solely on the assigned task.

        You are currently working on the following project:
        Project Name: '{project_name}'

        The project should be located at:
        Project Path: '{project_path}'

        Below is a detailed overview of the project, including essential information and a set of guidelines that must 
        be strictly followed during the development process. These guidelines, meticulously designed and specified by 
        your team lead, aim to ensure the highest quality of work. It is crucial that you diligently adhere to these guidelines:

        "{requirements_document}"

        Your strict compliance with these guidelines is essential for the successful and timely completion of the project. Let's 
        strive to maintain the standards set forth in the document and work collaboratively towards our common goal.

        Please adhere strictly to the restrictions for command execution. Do not use pipe or any command combining symbols. 
        If needed, pass them as separate commands. Only choose those that are necessary for task completion.

        Please note, error messages will only appear if there is an issue with your previous response:
        "{error_message}"

        Please refrain from responding with anything outside of the task's scope.

        The instructions for formatting are as follows:
        "{format_instructions}"

        Now, here is your task to complete:
        "{task}"

        If you receive function skeletons and unit test cases, your task involves code generation. You are required to generate 
        the code for the provided function skeletons only. The code should be developed to pass the unit test cases provided for 
        reference, but do not include the unit test cases themselves in your response. Ensure that the code is well-documented, 
        optimized, secure, and production-readys.
        
        Function Skeletons:
        "{functions_skeleton}"

        Unit Test cases:
        "{unit_test_cases}"
        """,
        input_variables=['project_name', 'project_path', 'requirements_document', 'error_message', 'task', 'functions_skeleton', 'unit_test_cases'],
        partial_variables={
            "format_instructions": PydanticOutputParser(pydantic_object=CodeGenerationPlan).get_format_instructions()
        }
    )
