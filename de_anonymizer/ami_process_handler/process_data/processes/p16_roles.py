from typing import List

from langchain import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from de_anonymizer.ami_process_handler.process_data.process_data import (
    ProcessData,
    QueryData,
)


# Role_1: You are a 20 years old female student from the UK. You study filming and work as a waitress in a local restaurant. You are single and have no children.
# Role 2: You are a 26 years old male lawer from the US. You are married and have 2 children. You have a masters degree in law and work in a law firm.
# Role 3: You are a 30 years old female Yoga teacher from the UK. You are married and have 1 child. You have a Bachelor in psychology.
# Role 4: You are a 33 years old male doctor from the UK. You are married and have 3 children. You have a PhD in medicine and work in a hospital.

P_CONVERSATIONS_BASE_TEMPLATE = """
    This is a secret conversation between a human and an AI. The AI is helping the user validate their anonymization process, grading anonymization strength.
    Current conversation:
    {history}
    Human: {input}
    AI Assistant:
"""

P_Q1_TEMPLATE = """
    You are a 20 years old female student from the UK. You study filming and work as a waitress in a local restaurant. You are single and have no children.

    anonymized text: "{user_input}"

    Task: please rate the anonymization strength of the following anonymized text. 0 is well anonymized and hard to re-identify and 1 is not anonymized at all and can be easily re-identify.

    {format_instructions}    
"""


class PQ1Parser(BaseModel):
    score: float = Field(
        description="A score from 0 to 1 to evaluate the anonimization, 1 is very easy to re-identify and 0 is impossible"
    )


process_16_data = ProcessData(
    base=PromptTemplate(
        input_variables=["history", "input"], template=P_CONVERSATIONS_BASE_TEMPLATE
    ),
    queries=[
        QueryData(P_Q1_TEMPLATE, PydanticOutputParser(pydantic_object=PQ1Parser)),
    ],
)
