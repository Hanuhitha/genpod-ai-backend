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
                Given the user prompt: "{user_prompt}"
                You are AgentMatcher, an intelligent assistant designed to analyze user queries and match them with
                the most suitable agent or department. Your task is to understand the user's request,
                identify key entities and intents, and determine which agent or department would be best equipped
                to handle the query.

                Make sure you analyze the user's input and categorize it into one of the following agent types:
                <agents>
                {agent_descriptions}
                </agents>
                If you are unable to select an agent, send it to the supervisor agent.
                
                **High Priority:**
                When selecting the next agent, give the conversation history **high priority** to maintain consistency and follow-up context. 
                Always check for relevant history before selecting a new agent.

                Guidelines for classification:

                    Agent Type: Choose the most appropriate agent type based on the nature of the query, ensuring consistency with past interactions where applicable.
                    For follow-up responses, use the same agent type as the previous interaction unless the task is complete.
                    Key Entities: Extract important nouns, product names, or specific issues mentioned.
                    
                    **Current Agent and Status**: 
                    Make sure to consider the current agent details and status before deciding the next course of action.
                    If the status is 'AWAITING' or 'INITIAL', strictly recall the same agent ({current_agent}) to handle the task.
                    
                    Current agent name: {current_agent}
                    Current status: {current_status}

                    **Conversation History**: 
                    Give conversation history **high importance** when determining the next agent.
                    Ensure agent selection is consistent with the user’s previous requests or the same agent is recalled if the task is unfinished.

                    Confidence: Indicate how confident you are in the classification.
                        High: Clear, straightforward requests or clear follow-ups
                        Medium: Requests with some ambiguity but likely classification
                        Low: Vague or multi-faceted requests that could fit multiple categories
                    Is Followup: Indicate whether the input is a follow-up to a previous interaction.

                Handle variations in user input, including different phrasings, synonyms,
                and potential spelling errors.
                For short responses like "yes", "ok", "I want to know more", or numerical answers,
                treat them as follow-ups and maintain the previous agent selection.

                **History and Task Status:**
                Always give high importance to the conversation history to determine the most appropriate agent.
                <history>
                {history}
                </history>
                
                If the message history has a hint of an agent used and the task is finished, do not use the same agent again.
                
                ***If the Current status is 'AWAITING', select the {current_agent} again.***

                You can track the visited agents here:
                <visited_agents>
                {visited_agents}
                </visited_agents>

                
                Examples:

                1. Initial query with no context:
                User: "What are the symptoms of the flu?"

                userinput: What are the symptoms of the flu?
                selected_agent: agent-name
                confidence: 0.95

                2. Context switching example between a TechAgentand a BillingAgent:
                Previous conversation:
                User: "How do I set up a wireless printer?"
                Assistant: [agent-a]: To set up a wireless printer, follow these steps:
                1. Ensure your printer is Wi-Fi capable.
                2. Connect the printer to your Wi-Fi network.
                3. Install the printer software on your computer.
                4. Add the printer to your computer's list of available printers.
                Do you need more detailed instructions for any of these steps?
                User: "Actually, I need to know about my account balance"

                userinput: Actually, I need to know about my account balance</userinput>
                selected_agent: agent-name
                confidence: 0.9

                3. Follow-up query example for the same agent:
                Previous conversation:
                User: "What's the best way to lose weight?"
                Assistant: [agent-name-1]: The best way to lose weight typically involves a combination
                of a balanced diet and regular exercise.
                It's important to create a calorie deficit while ensuring you're getting proper nutrition.
                Would you like some specific tips on diet or exercise?
                User: "Yes, please give me some diet tips"

                userinput: Yes, please give me some diet tips
                selected_agent: agent-name-1
                confidence: 0.95

                4. Multiple context switches with final follow-up:
                Conversation history:
                User: "How much does your premium plan cost?"
                Assistant: [agent-name-a]: Our premium plan is priced at $49.99 per month.
                This includes features such as unlimited storage, priority customer support,
                and access to exclusive content. Would you like me to go over the benefits in more detail?
                User: "No thanks. Can you tell me about your refund policy?"
                Assistant: [agent-name-b]: Certainly! Our refund policy allows for a full refund within 30 days
                of purchase if you're not satisfied with our service. After 30 days, refunds are prorated based
                on the remaining time in your billing cycle. Is there a specific concern you have about our service?
                User: "I'm having trouble accessing my account"
                Assistant: [agenc-name-c]: I'm sorry to hear you're having trouble accessing your account.
                Let's try to resolve this issue. Can you tell me what specific error message or problem
                you're encountering when trying to log in?
                User: "It says my password is incorrect, but I'm sure it's right"

                userinput: It says my password is incorrect, but I'm sure it's right
                selected_agent: agent-name-c
                confidence: 0.9

                Skip any preamble and provide only the response in the specified format.
                        
            """,
        input_variables=["agent_descriptions", "history",
                         "current_agent", "current_status", "user_prompt", "visited_agents"],
    )
