""" Contain all the prompts needed by the RAG Agent"""
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate


class RAGPrompts():
    # Prompt 1
    retriever_grader_prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
        Here is the retrieved document: \n\n {document} \n\n
        Here is the user question: {question} \n
        If the document contains keywords related to the user question, grade it as relevant. \n
        It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
        Provide the binary score as a JSON with a single key 'score', without any markdown formatting or code blocks and no premable or explanation.""",
        input_variables=["question", "document"],
    )

    # Prompt 2
    halucination_grader_prompt = PromptTemplate(
        template="""You are a grader assessing whether an answer is grounded in / supported by a set of facts. \n 
        Here are the facts:
        \n ------- \n
        {documents} 
        \n ------- \n
        Here is the answer: {generation}
        Give a binary score 'yes' or 'no' score to indicate whether the answer is grounded in / supported by a set of facts. \n
        Provide the binary score as a JSON with a single key 'score', without any markdown formatting or code blocks and no preamble or explanation.""",
        input_variables=["generation", "documents"],
    )

    # Prompt 3
    re_write_prompt = PromptTemplate(
        template="""You a question re-writer that converts an input question to a better version that is optimized \n 
        for vectorstore retrieval. Look at the initial and formulate an improved question. \n
        Here is the initial question: \n\n {question}. Improved question with no preamble: \n """,
        input_variables=["generation", "question"],
    )

    # Prompt 4
    answer_grader_prompt = PromptTemplate(
        template="""You are a grader assessing whether an answer is useful to resolve a question. \n 
        Here is the answer:
        \n ------- \n
        {generation} 
        \n ------- \n
        Here is the question: {question}
        Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question. \n
        Provide the binary score as a JSON with a single key 'score', without any markdown formatting or code blocks and no preamble or explanation.""",
        input_variables=["generation", "question"],
    )

    # Prompt 5
    rag_template = """\
    Use the following context to answer the user's query. If you cannot answer, please respond with 'I don't know'.

    User's Query:
    {question}

    Context:
    {context}
    """

    rag_generation_prompt = ChatPromptTemplate.from_template(rag_template)
