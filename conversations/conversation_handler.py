from dataclasses import dataclass
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

from de_anonymizer.ami_process_handler.process_data.process_data import QueryData

from enum import Enum

class ResponseStatus(Enum):
    SUCCESS = 0
    ERROR = 1

class ConversationHandler:
    def __init__(self, llm_chat_model) -> None:
        self.conversation = None
        self.llm_chat_model = llm_chat_model
    

    def start_conversation(self, base_template: PromptTemplate):
        self.conversation = ConversationChain(
            llm=self.llm_chat_model,
            memory=ConversationBufferMemory(return_messages=True),
            prompt=base_template
        )

    def send_new_message(self, query: QueryData, user_input: str="", **kwargs):
        prompt = query.get_prompt()
        
        if len(kwargs) == 0:
            # Process 1, 2
            prompt = prompt.format(user_input=user_input, format_instructions=query.parser.get_format_instructions())
        else: 
            # Process 3
            prompt = prompt.format(
                user_input=user_input,
                example_score_1=kwargs["example_score_1"],
                example_score_0=kwargs["example_score_0"],
                example_score_05=kwargs["example_score_05"],
                format_instructions=query.parser.get_format_instructions())
        parser = query.parser
        response = self.conversation.predict(input=prompt.content)
        try:
            return {'status': ResponseStatus.SUCCESS, 'data': parser.parse(response)}
        except:
            return {'status': ResponseStatus.ERROR, 'data': response}


    def end_conversation(self):
        self.conversation.memory.clear()
