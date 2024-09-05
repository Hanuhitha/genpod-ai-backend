"""
"""

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.segregation import Segregation


class SegregatorPrompts:

    segregation_prompt: PromptTemplate =PromptTemplate(
        template="""
    Objective:
    You are an intelligent assistant designed to assess whether completing a work package requires writing any functions. Use contextual understanding to accurately evaluate the tasks within the work package.

    Instructions:

    Identify Function Requirement:
        Determine whether any part of the work package involves writing functions (code blocks that perform specific tasks) in the given programming language.

    Assessment Criteria:
        Requires Writing Functions: The task involves creating new functions, modifying existing ones, or utilizing functions to achieve specific objectives.
        Does Not Require Writing Functions: The task does not involve writing or modifying functions, but may involve other activities such as configuration, documentation, or design.

    Response Format:
        Clearly state whether the work package requires writing functions or not.
        Provide a brief explanation if necessary to justify the assessment.

     The instructions for formatting are as follows:
    {format_instructions}

    This is the work package you have to classify using the description and the details provided classisfy 

    "{work_package}"

    """,
            input_variables=['work_package' ],
            partial_variables= {
                "format_instructions": PydanticOutputParser(pydantic_object=Segregation).get_format_instructions()
            }
        )
    
