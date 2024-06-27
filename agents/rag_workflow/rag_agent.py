from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from rag_workflow.rag_state import RAGState
from rag_workflow.rag_prompts import RAGPrompts

class RAGAgent():
    def __init__(self, llm, collection_name, persist_directory=None):
        assert persist_directory is not None, "Currently only Local Chroma VectorDB is supported"
        self.mismo_vectorstore = Chroma(
                            collection_name = collection_name,
                            persist_directory = persist_directory,
                            embedding_function = OpenAIEmbeddings())
        self.retriever = self.mismo_vectorstore.as_retriever(search_kwargs={'k': 20})
        self.llm = llm
        
        # Document retrieval Grader chain
        self.retrieval_grader = RAGPrompts.retriever_grader_prompt | self.llm | JsonOutputParser()
        
        # Halucination Grader chain
        self.hallucination_grader = RAGPrompts.halucination_grader_prompt | self.llm | JsonOutputParser()

        # Question Re-writer chain
        self.question_rewriter = RAGPrompts.re_write_prompt | self.llm | StrOutputParser()

        # Answer grader from the chain
        self.answer_grader = RAGPrompts.answer_grader_prompt | self.llm | JsonOutputParser()

        # RAG Answering chain 
        self.rag_generation_chain = (
            RAGPrompts.rag_generation_prompt
            | self.llm
            | StrOutputParser()
        )

    def retrieve(self, state: RAGState):
        """
        Retrieve documents

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        print("---RETRIEVE---")
        question = state["question"]

        # Retrieval
        documents = self.retriever.get_relevant_documents(question)
        return {**state, "documents": documents, "question": question}

    def generate(self, state: RAGState):
        """
        Generate answer

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        print("---GENERATE---")
        question = state["question"]
        documents = state["documents"]

        # RAG generation
        generation = self.rag_generation_chain.invoke({"context": documents, "question": question})
        return {**state, "documents": documents, "question": question, "generation": generation}

    def grade_documents(self, state: RAGState):
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with only filtered relevant documents
        """

        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        question = state["question"]
        documents = state["documents"]

        # Score each doc
        filtered_docs = []
        for d in documents:
            score = self.retrieval_grader.invoke(
                {"question": question, "document": d.page_content}
            )
            grade = score["score"]
            if grade == "yes":
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                continue
        return {**state, "documents": filtered_docs, "question": question}

    def transform_query(self, state: RAGState):
        """
        Transform the query to produce a better question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates question key with a re-phrased question
        """

        print("---TRANSFORM QUERY---")
        question = state["question"]
        documents = state["documents"]

        # Re-write question
        better_question = self.question_rewriter.invoke({"question": question})
        return {**state, "documents": documents, "question": better_question}

    def decide_to_generate(self, state: RAGState):
        """
        Determines whether to generate an answer, or re-generate a question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Binary decision for next node to call
        """

        print("---ASSESS GRADED DOCUMENTS---")
        question = state["question"]
        filtered_documents = state["documents"]

        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            print(
                "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
            )
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            print("---DECISION: GENERATE---")
            return "generate"

    def grade_generation_v_documents_and_question(self, state: RAGState):
        """
        Determines whether the generation is grounded in the document and answers question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Decision for next node to call
        """

        print("---CHECK HALLUCINATIONS---")
        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]

        score = self.hallucination_grader.invoke(
            {"documents": documents, "generation": generation}
        )
        grade = score["score"]

        # Check hallucination
        if grade == "yes":
            print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
            # Check question-answering
            print("---GRADE GENERATION vs QUESTION---")
            score = self.answer_grader.invoke({"question": question, "generation": generation})
            grade = score["score"]
            if grade == "yes":
                print("---DECISION: GENERATION ADDRESSES QUESTION---")
                return "useful"
            else:
                print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
                return "not useful"
        else:
            print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
            return "not supported"