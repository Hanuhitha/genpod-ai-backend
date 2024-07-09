""" Define the prompt template for the Planner """
from langchain.prompts import PromptTemplate

class PlannerPrompts():
    backlog_planner_prompt = PromptTemplate(
        template="""Given the deliverable, additional context and feedback, provide work packages of tasks needed to complete this deliverable.
        feedback is only present if you did not provide output in appropriate format previously.

        Deliverable: {deliverable}
        Additional context: {context}
        Feedback: {feedback}

        Give a Deliverable and Additional context, you should return the output similar to the example_output below.
        example_output: ['workpackage1','workpackage2','workpackage3']

        Provide the list of backlog tasks exactly as the example output format above for this deliverable.

        To complete the task accurately it is important to not assume anything and ask questions when any information is missing.
        Provide the list of backlog of tasks for this deliverable that I can convert using ast.literal_eval(example_output)""",
        input_variables=["deliverable", "context", "feedback"]
    )

    detailed_requirements_prompt = PromptTemplate(
        template="""As a software development planner, your task is to analyze the given backlog item for the deliverable and provide detailed technical requirements in the specified JSON format. If you need more information, ask specific questions.
        Feedback is only present if you did not provide output in appropriate format previously.
        
        Backlog Item: {backlog}
        Deliverable: {deliverable}
        Additional Context: {context}
        Feedback: {feedback}

        Instructions:
        - If you have enough information, provide the detailed technical requirements as a JSON object with the following structure. Avoid adding generic comments within the JSON Object and use strict json format to add comments about any object:
        {{
            "description": "Detailed description of the task",
            "name": "Name of the service or component",
            "language": "Programming language to be used",
            "restConfig": {{
            "server": {{
                "sqlDB": "Database type",
                "port": "Port number",
                "resources": [
                {{
                    "name": "Resource name",
                    "allowedMethods": ["POST", "LIST", "GET", "PUT", "DELETE"],
                    "fields": {{
                    "FieldName": {{
                        "datatype": "Data type of the field"
                    }},
                    ...
                    }}
                }},
                ...
                ]
            }},
            "framework": "Framework to be used"
            }},
            "LICENSE_URL": "URL to the license",
            "LICENSE_TEXT": "Text of the license"
        }}

        - If you need more information, respond with a JSON object containing a single detailed question that can be used to retrieve additional information from RAG or can be asked to the Architect of the project:
        {{
            "question": "A single, detailed question that covers all the information you need to proceed with the technical requirements"
        }}

        Remember:
        - Focus on technical aspects and implementation details.
        - Consider architectural decisions, coding standards, and best practices.
        - Include any necessary API specifications, database schema changes, or UI/UX considerations.
        - If any critical technical information is missing, ask specific questions to clarify.
        - Ensure all requirements are clear, measurable, and testable from a development perspective.

        Your response:
        """,
            input_variables=["backlog", "deliverable", "context", "feedback"]
        )
