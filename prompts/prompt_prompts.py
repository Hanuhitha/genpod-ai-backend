"""
"""
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

from pydantic_models.prompt_models import Prompt_Generation, Decision_Agent


class PromptPrompts:
    prompt_generation_prompt: PromptTemplate = PromptTemplate(
        template="""
            You are a Prompt Agent responsible for refining user-provided prompts related to coding projects.
            Your task is to improve the clarity, structure, and detail of the provided prompt according to the predefined structure.

            User's Original Request:
            {original_user_input}
            
            Conversations (User Feedback):
            {messages}
            
            Objective:
            Enhance the user's original request using the provided structure. Ensure the prompt is clear, well-organized, and includes all essential details.

            Predefined Structure:
            1. **Project Overview**: 
                - Provide a concise summary, including the project's purpose and the problem it aims to solve.
            2. **Technology Stack**:
                - Specify technologies, services, databases, web servers, and hosting details mentioned by the user.
            3. **Functional Requirements**:
                - Outline core functionalities like request handling, data processing, and response generation.
            4. **Technical Specifications**:
                - Detail API specifications, database connections, and hosting environment requirements.
            5. **Validation & Error Handling**:
                - Include input validation checkpoints, data formats, and error handling mechanisms.
            6. **User Stories & Acceptance Criteria**:
                - Break down the system into specific user stories, defining actions the user should be able to perform.
                - Each user story should be in the following format:
                
                  **User Story:** 
                  As a [type of user], I want to [action to achieve] so that [goal to achieve].
                  
                  **Acceptance Criteria:**
                  - List of conditions or requirements that must be met for the user story to be considered complete.
                  - These criteria should be clear, testable, and measurable.
                
                **Example of User Story & Acceptance Criteria**:
                **User Story**: 
                As a **developer**, I want to **submit a project prompt** so that **the prompt is refined and used for AI-based generation**.
                
                **Acceptance Criteria**:
                - The user should be able to submit a prompt via the command line interface (CLI).
                - The system should store the submitted prompt in the database.
                - The system should provide feedback on the status of the prompt submission.
                - If the system encounters an error (like invalid input), it should display an error message to the user.
                - If the WebSocket connection fails, the user should be notified and reconnected automatically.

            Instructions for Improvement:
            - Use clear and precise language.
            - Correct grammatical and spelling errors.
            - Add missing details based on user input.
            - Adhere to the predefined structure and make the prompt concise and unambiguous.

            Output Format:
            Present the improved prompt in structured paragraphs or bullet points, following the predefined structure.
            
         output format instructions:
            '{format_instructions}'
            """,
        input_variables=['original_user_input', 'messages'],
        partial_variables={
            "format_instructions": PydanticOutputParser(pydantic_object=Prompt_Generation).get_format_instructions()
        }
    )


    decision_agent_prompt: PromptTemplate = PromptTemplate(
        template="""
         You are the decision agent. Your task is to determine whether the refined prompt needs further modification based on the user's feedback.

            Original User Request:
            {original_user_input}
            
            Refined Prompt and User Feedback:
            {messages}
            
            Based on the given informations, and the user's feedback, decide if the current prompt is good enough or if it needs improvement.

            Output Format:
            - Respond with "YES" if the prompt is good enough and no further changes are needed.
            - Respond with "NO" if the prompt needs further modification . 
            - Respond with "NO" if the user is still thinking and gives a black response.
            output format instructions:
            '{format_instructions}'
            """,
        input_variables=['original_user_input', 'messages'],
        partial_variables={
            "format_instructions": PydanticOutputParser(pydantic_object=Decision_Agent).get_format_instructions()
        }

    )
