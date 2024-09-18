"""Script to generate Requirements Document in parts using LLM and then combining them to create a complete requirements_document. 
    Move this file to src folder before running, to avoid any import errors."""

import os

from dotenv import load_dotenv
from langchain.schema.runnable import RunnablePassthrough
from langchain_openai import ChatOpenAI

from prompts.architect_prompts import ArchitectPrompts

load_dotenv()

def create_full_document(result):
    """
    Create a full Markdown document from the SequentialChain results.
    """
    document = f"""
# Project Requirements Document

{result['project_overview']}

{result['architecture']}

{result['folder_structure']}

{result['microservice_design']}

{result['tasks']}

{result['standards']}

{result['implementation_details']}

{result['license']}
        """
    return document

def write_to_file(content, filename='requirements.md'):
    """
    Write the content to a file.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__=="__main__":
    # Get Architect Prompts
    architect_prompts = ArchitectPrompts()

    # Initialize your LLM
    llm = ChatOpenAI(model="gpt-4o-2024-05-13", temperature=0.3, max_retries=5, streaming=True, seed=4000, top_p=0.4)

    # Ensure each chain has the correct input_variables and output_key
    project_overview_chain = architect_prompts.project_overview_prompt | llm | (lambda x: x.content)  # This step extracts only the content part from the llm output AImessage
    
    architecture_chain = architect_prompts.architecture_prompt | llm | (lambda x: x.content)

    folder_structure_chain = architect_prompts.folder_structure_prompt | llm | (lambda x: x.content)

    microservice_design_chain = architect_prompts.microservice_design_prompt | llm | (lambda x: x.content)

    tasks_breakdown_chain = architect_prompts.tasks_breakdown_prompt | llm | (lambda x: x.content)

    standards_chain = architect_prompts.standards_prompt | llm | (lambda x: x.content)

    implementation_details_chain = architect_prompts.implementation_details_prompt | llm | (lambda x: x.content)

    license_legal_chain = architect_prompts.license_details_prompt | llm | (lambda x: x.content)

    overall_chain = (
        RunnablePassthrough.assign(project_overview=project_overview_chain)
        | RunnablePassthrough.assign(architecture=architecture_chain)
        | RunnablePassthrough.assign(folder_structure=folder_structure_chain)
        | RunnablePassthrough.assign(microservice_design=microservice_design_chain)
        | RunnablePassthrough.assign(tasks=tasks_breakdown_chain)
        | RunnablePassthrough.assign(standards=standards_chain)
        | RunnablePassthrough.assign(implementation_details=implementation_details_chain)
        | RunnablePassthrough.assign(license=license_legal_chain)
    )

    # Run the chain
    req_document_in_parts = overall_chain.invoke(input={
        "user_request": 'I want to develop a Title Requests Micro-service adhering to MISMO v3.6 standards to handle get_title service using GET REST API Call in .NET?',
        "task_description": 'This task is part of Project Initiation Phase and has two deliverables, a project requirements document and a list of project deliverables.\n\n            Do not assume anything and request for additional information if provided information is not sufficient to complete the task or something is missing.',
        "additional_information": 'any additional info goes here',
        "license_text": "Property of XYZ COMPANY"
    })

    # Create the full document
    full_document = create_full_document(req_document_in_parts)

    # Write the document to a file
    write_to_file(full_document)

    print(f"Requirements document has been written to {os.path.abspath('./requirements.md')}")
