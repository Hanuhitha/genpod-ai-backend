"""
This module contains all the prompt templates for the Architect agent.

Each prompt in this module is designed to guide the Architect agent in 
performing its tasks. The prompts cover a wide range of scenarios, from 
analyzing user input and creating comprehensive requirements documents, to 
breaking down projects into independent tasks and enforcing best practices in
microservice architecture, project folder structure, and clean-code development.

The prompts are used to instruct the Architect agent on how to respond to user 
inputs and how to structure its outputs. They are essential for ensuring that 
the Architect agent can effectively assist users in implementing their projects.
"""
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.architect_models import (ProjectDetails, QueryResult, TaskOutput,
                                     TasksList)


class ArchitectPrompts:
    """
    ArchitectPrompts class contains templates for guiding the Architect agent in its tasks.
    
    It includes templates for initial project requirements generation and for providing additional 
    information during project implementation. These templates ensure that the Architect agent can 
    effectively assist users in implementing their projects, adhering to best practices in 
    microservice architecture, project folder structure, and clean-code development.
    """

    additional_info_prompt: PromptTemplate = PromptTemplate(
        template="""
        As a Solution Architect, you have previously prepared comprehensive requirements documents 
        for your team members to work on the project. You should not answer anything out of the 
        provided context.

        We would appreciate your response to the following question:
        '{question}'

        For your reference, here are the Requirements Documents you previously prepared:
        '{requirements_document}'

        Please note, an error message will only be provided if there was an issue with your previous output:
        {error_message}

        output format instructions:
        '{format_instructions}'
        """,
        input_variables=['question', 'requirements_document', 'error_message'],
        partial_variables={
            "format_instructions": PydanticOutputParser(pydantic_object=QueryResult).get_format_instructions()
        }
    )

    tasks_separation_prompt: PromptTemplate = PromptTemplate(
        template="""
            You have previously generated a well-formatted requirements document in markdown 
            format. As a part of it you also prepared deliverables for the project:

            '{tasks}'

            Your task is to convert the deliverables from this markdown document into a list or an array. 
            Each task should be copied exactly as it appears in the markdown document and transformed 
            into an item of an list or array. No modifications should be made to the statements.

            Error messages will only be present if there is an issue with your previous response. 
            '{error_message}'

            "Example:
            [Task1, Task2, Task3, .... TaskN]
            "
            output format instructions:
            '{format_instructions}'
        """,
        input_variables=['tasks', 'error_message'],
        partial_variables={
            "format_instructions": PydanticOutputParser(pydantic_object=TasksList).get_format_instructions()
        }
    )

    project_overview_prompt: PromptTemplate = PromptTemplate(
        template=""" Given the user request: "{user_request}"
            Supervisor expectations: "{task_description}"
            Additional information: "{additional_information}"

            As a Solution Architect, provide a comprehensive project overview. Include:
            1. A brief description of the project's purpose and goals
            2. The main features or functionalities to be implemented
            3. What schema definition models are needed to implement this service.

            Format your response in markdown, starting with a "## Project Overview" heading.
            
            output format instructions:
            {format_instructions}
        """,
        input_variables=['user_request','task_description','additional_information'],
        partial_variables = {
                "format_instructions": PydanticOutputParser(pydantic_object=TaskOutput).get_format_instructions()
        }
    )

    architecture_prompt: PromptTemplate = PromptTemplate(
        template="""Based on the project overview, describe the high-level architecture for this microservice-based project. Include:
            Project Overview: "{project_overview}"

            1. A diagram or detailed description of the microservice architecture
            2. Key components, data models and their interactions
            3. Data flow between services
            4. External integrations or APIs
            5. Scalability and reliability considerations

            Format your response in markdown, starting with a "## Architecture" heading.
                        
            output format instructions:
            {format_instructions}
        """,
        input_variables=['project_overview'],
        partial_variables = {
            "format_instructions": PydanticOutputParser(pydantic_object=TaskOutput).get_format_instructions()
        }
    )

    folder_structure_prompt: PromptTemplate = PromptTemplate(
        template="""
        Given the project overview and architecture:

        Project Overview:
        {project_overview}

        Architecture:
        {architecture}

        Propose a detailed folder structure for this microservice project, adhering to best practices. Include:
        1. Root-level directories
        2. Service-specific directories
        3. Common or shared directories
        4. Test directories
        5. Configuration file locations
        6. Explanation of the purpose for each major directory

        Format your response in markdown, starting with a "## Folder Structure" heading.
                                
        output format instructions:
        {format_instructions}
        """,
        input_variables=["project_overview", "architecture"],
        partial_variables = {
            "format_instructions": PydanticOutputParser(pydantic_object=TaskOutput).get_format_instructions()
        }
    )

    microservice_design_prompt: PromptTemplate = PromptTemplate(
        template="""
            Based on the following project overview and architecture:

            Project Overview:
            {project_overview}
            
            Architecture:
            {architecture}

            For each microservice identified, provide:
            1. Service name and primary responsibility
            2. Key endpoints or functions
            3. Data models or schemas
            4. Internal components or modules
            5. Dependencies on other services or external systems

            Format your response in markdown, starting with a "## Microservice Design" heading, with subheadings for each service.
                                            
            output format instructions:
            {format_instructions}
            """,
        input_variables=["project_overview","architecture"],
        partial_variables = {
            "format_instructions": PydanticOutputParser(pydantic_object=TaskOutput).get_format_instructions()
        }
    )

    tasks_breakdown_prompt: PromptTemplate = PromptTemplate(
        template="""
            Given the project overview, architecture, and microservice design:

            Project Overview:
            {project_overview}

            Architecture:
            {architecture}

            Microservice Design:
            {microservice_design}

            Break down the project into detailed, self-contained deliverables that team members can work on. Key is to not miss any technical specification for each deliverable, provide:
            1. Deliverable name
            2. Detailed description of what needs to be done
            3. Technical requirements or specifications

            Format your response in markdown, starting with a "## Tasks" heading, with each task as a subheading.
            
            output format instructions:
            {format_instructions}            
            """,
        input_variables=["project_overview", "architecture", "microservice_design"],
        partial_variables = {
            "format_instructions": PydanticOutputParser(pydantic_object=TaskOutput).get_format_instructions()
        }        
    )

    standards_prompt: PromptTemplate = PromptTemplate(
        template="""
            Considering the user request: "{user_request}"
            And the supervisor expectations: "{task_description}"

            Outline the standards to be followed in this project, including:
            1. 12-Factor Application Standards: Explain how each factor applies to this project
            2. Clean Code Standards: Specific practices for maintaining clean, readable code
            3. Code Commenting Standards: Guidelines for effective code documentation
            4. Programming Language Specific Standards: Conventions for the chosen language(s)
            5. User Requested Standards: Any additional standards specified by the user or supervisor

            Format your response in markdown, starting with a "## Standards" heading, with subheadings for each category.
            
            output format instructions:
            {format_instructions}
            """,
        input_variables=["user_request", "task_description"],
        partial_variables = {
            "format_instructions": PydanticOutputParser(pydantic_object=TaskOutput).get_format_instructions()
        }            
    )

    implementation_details_prompt: PromptTemplate = PromptTemplate(
        template="""
            Based on the following project details:

            Architecture:
            {architecture}

            Microservice Design:
            {microservice_design}

            Folder Structure:
            {folder_structure}

            Provide specific implementation details for:
            1. list of required source files
            2. list of Configuration files
            3. list of Unit test approach and files
            4. OpenAPI specification (provide a sample structure in YAML)
            5. Dependency management (specify package manager and provide a sample file)
            6. Dockerfile contents
            7. Contents for .dockerignore and .gitignore files

            Format your response in markdown, starting with a "## Implementation Details" heading, with subheadings for each category.
            
            output format instructions:
            {format_instructions}
            """,
        input_variables=["architecture", "microservice_design", "folder_structure"],
        partial_variables = {
            "format_instructions": PydanticOutputParser(pydantic_object=TaskOutput).get_format_instructions()
        }            
    )

    license_details_prompt: PromptTemplate = PromptTemplate(
        template="""
            Considering the user request: "{user_request}"
            And the License Text: "{license_text}"

            Specify the license to be used for this project.

            Format your response in markdown, starting with a "## License and Legal Considerations" heading.
            
            output format instructions:
            {format_instructions}
            """,
        input_variables=["user_request", "license_text"],
        partial_variables = {
            "format_instructions": PydanticOutputParser(pydantic_object=TaskOutput).get_format_instructions()
        }            
    )

    project_details_prompt: PromptTemplate = PromptTemplate(
        template="""
        Given the user's request: "{user_request}"

        Please suggest a project name that adheres to the naming standards. 
        
        Error messages will only be present if there is an issue with your previous response. 
        '{error_message}'

        Output format instructions:
        {format_instructions}
        """,
        input_variables=['user_request', 'error_message'],
        partial_variables={
            "format_instructions": PydanticOutputParser(pydantic_object=ProjectDetails).get_format_instructions()
        }
    )
