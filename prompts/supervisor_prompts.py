""" Contain all the prompts needed by the Supervisor Agent"""
from langchain.prompts import PromptTemplate


class SupervisorPrompts():
    delegator_prompt = PromptTemplate(
        template="""You are a Supervisor of a team who always tracks the status of the project and the tasks \n 
        Active team members are: \n\n {team_members} \n\n
        What do each team memeber do:\n
        Architect: ['Creates Requirements document','Creates Deliverables','Answer any additional information']
        RAG: Contains proprietary information so must be called when such information is needed

        If the document contains keywords related to the user question, grade it as relevant. \n
        It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
        Provide the binary score as a JSON with a single key 'score' and no premable or explanation.""",
        input_variables=["question", "document"],
    )

    response_evaluator_prompt = PromptTemplate(
        template="""You are a Supervisor responsible for evaluating the completeness of responses from team members. Your task is to determine if a given response requires additional information or clarification.

        Current team members: {team_members}

        Response to evaluate: {response}

        Original user query: {user_query}

        Evaluation criteria:
        1. Does the response fully address the user's query?
        2. Is the information provided clear and comprehensive?
        3. Are there any obvious gaps or missing details in the response?
        4. Would the user likely need to ask follow-up questions based on this response?

        Provide a binary assessment as a JSON with a single key 'needs_additional_info'. Use 'true' if the response requires more information, and 'false' if it's complete and satisfactory. Do not include any explanation or preamble in your output.

        Example output:
        {"needs_additional_info": true}
        or
        {"needs_additional_info": false}""",
        input_variables=["team_members", "response", "user_query"],
    )

    architect_call_prompt = PromptTemplate(
        template="""This task is part of Project Initiation Phase and has two deliverables, a project requirements document and a list of project deliverables.\n
            Do not assume anything and request for additional information if provided information is not sufficient to complete the task or something is missing."""
    )

    additional_info_req_prompt = PromptTemplate(
        template="""A fellow agent is stuck with something and is requesting additional info on the question"""
    )

    init_rag_questionaire_prompt = PromptTemplate(
        template="""Given the user prompt: "{user_prompt}", generate a comprehensive list of questions to query the knowledge base which is a vector DB.
        These questions should cover various aspects of the project requirements, technical specifications, and industry standards. Focus on the following areas:
            1. Industry standards and regulations:
            - What specific standards or regulations are relevant to this project?
            - How do these standards impact the design and implementation?

            2. Project-specific requirements:
            - What are the key components or features required for this project?
            - Are there any specific data structures or formats that need to be considered?

            3. Data management:
            - What type of data storage is most suitable for this project?
            - How should the data be structured for efficient retrieval and management?

            Create a list response which containes one well-defined question for each category that will help extract detailed information from our knowledge base to assist in creating a comprehensive requirements document.
            example output format: "['question1','question2','question3']"
            Use this additional context if an error exists in output: {context}
            """,
        input_variables=["user_prompt", "context"]
    )

    follow_up_questions = PromptTemplate(
        template="""Given the original user query and the initial RAG response:

                    User query: "{user_query}"

                    Initial RAG response:
                    {initial_rag_response}

                    Evaluate the response based on the following criteria:
                    1. Relevance to the original query
                    2. Completeness of information
                    3. Technical accuracy
                    4. Clarity and coherence

                    Determine if the response is complete or if a follow-up query is needed.

                    If the response is complete, output:
                    COMPLETE
                    [Provide a brief summary of why the response is considered complete]

                    If the response is incomplete or inadequate, output:
                    INCOMPLETE
                    [Briefly explain why the response is incomplete]
                    Follow-up Query: [Provide a single, focused query to retrieve all the missing information]

                    Example outputs:

                    COMPLETE
                    The response fully addresses the user's query about the Title Requests Micro-service, covering MISMO v3.6 standards, GET REST API implementation, and .NET specifics.

                    INCOMPLETE
                    The response lacks details on specific MISMO v3.6 data structures for title requests.
                    Follow-up Query: What are the key MISMO v3.6 XML elements and data structures required for implementing a Title Requests GET service in .NET?

                    Your evaluation and output:""",
        input_variables=["user_query", "initial_rag_response"]
    )

    ideal_init_rag_questionaire_prompt = PromptTemplate(
        template="""Given the user prompt: "{user_prompt}", generate a comprehensive list of questions to query the knowledge base which is a vector DB. 
        These questions should cover various aspects of the project requirements, technical specifications, and industry standards. Focus on the following areas:
            1. Industry standards and regulations:
            - What specific standards or regulations are relevant to this project?
            - How do these standards impact the design and implementation?

            2. Project-specific requirements:
            - What are the key components or features required for this project?
            - Are there any specific data structures or formats that need to be considered?

            3. Technical architecture:
            - What is the recommended architecture for this type of project?
            - Are there any specific design patterns or best practices to follow?

            4. API design (if applicable):
            - What are the best practices for designing the API for this service?
            - How should the API endpoints be structured?

            5. Implementation details:
            - What are the recommended frameworks or libraries for this project?
            - Are there any specific features of the chosen technology that align well with the project requirements?

            6. Data management:
            - What type of data storage is most suitable for this project?
            - How should the data be structured for efficient retrieval and management?

            7. Security and compliance:
            - What security measures should be implemented for this project?
            - Are there any specific compliance requirements to consider?

            8. Performance and scalability:
            - What are the expected performance metrics for this service?
            - How can we ensure scalability of the system?

            9. Testing and validation:
            - What types of tests should be implemented for this project?
            - How can we validate that the service meets all requirements and standards?

            10. Documentation and specifications:
                - What should be included in the project documentation?
                - Are there any standard tools or formats recommended for documentation in this domain?

            Create a list response which containes one well-defined question for each category that will help extract detailed information from our knowledge base to assist in creating a comprehensive requirements document.
            example output format: "['question1','question2','question3']"
            Use this additional context if an error exists in output: {context}
            """,
        input_variables=["user_prompt", "context"]
    )

    classifier_prompt = PromptTemplate(
        template="""
        User input {user_prompt}
                You are AgentMatcher, an intelligent assistant designed to analyze the project flow to match the query with the most suitable agent. 
                Your task is to understand the project flow, identify key entities and intents, and determine which agent would be best equipped at any given point based on the status provided and flow of interactions.
                

                Categorize the agent into one of the following agent types: <agents> {agent_descriptions} </agents>

                High Priority:
                1. When selecting the next agent, give the project flow high priority to maintain consistency and follow-up context. Always check for relevant history before selecting a new agent.
                2. Select your agent also basing on the flags.
            Guidelines for Classification:
                Project Flow: Understand the project flow to know the step by step process. 
                Project Flow: {project_flow}
                Agent Type: Choose the most appropriate agent type based on the project flow, ensuring consistency with past interactions where applicable.
                 High Priority: Look at the data here serialized output below and extract boolean flag information from it
                to select the next agent. 
                {flags}
                Current Agent and Status:
                Consider the current agent details and status before deciding the next course of action.
                Check the project status and refer to the message history to determine the course of action.
                    Calling Agent: {current_agent}
                    task status: {current_status}
                    Project status: {project_status}
                    Conversation History: {history}
                    
                Confidence: Indicate how confident you are in the classification.
                    High: Clear, straightforward requests or follow-ups
                    Medium: Requests with some ambiguity but likely classification
                    Low: Vague or multi-faceted messages that could fit multiple categories
                 Reason: Provide a brief explanation of why a particular agent was selected based on the project flow and other indicators like the project status, task status and current agent. Mention the flags in the reason.

                You can track the visited agents here:
                <visited_agents>
                {visited_agents}
                </visited_agents>           
                
                
                Skip any preamble and provide only the response in the specified format.
                    
                        """,
        input_variables=["agent_descriptions", "history",
                         "current_agent", "current_status", "user_prompt", "visited_agents", "project_status", "project_flow", "flags"],
    )
