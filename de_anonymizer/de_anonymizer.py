import os
import langchain
import pandas as pd
from de_anonymizer.ami_process_handler.ami_process_handler import AMI_process_handler
from conversations.conversation_handler import ConversationHandler, ResponseStatus
from de_anonymizer.data_handler.data_handler import DataHandler

from utils import get_local_keys, load_google_search_tool, load_model


class DeAnonymizer:
    """
    Class of a de-anonymizer.
    """

    def __init__(
        self,
        llm_name: str,
        self_guide: bool = False,
        google: bool = False,
        debug: bool = False,
        verbose: bool = False,
        process_id: int = 1,
        should_handle_data: bool = False,
        temperature: float = 0.5,
        **kwargs,
    ):
        """
        Create a new instance of a de-anonymiser.
        :param llm: The LLM to use.
        :param self_guide: Whether to use self-guide or not.
        :param google: Whether to use google search or not.
        :param debug: Whether to use debug mode or not.
        :param verbose: Whether to use verbose mode or not.
        :param process_id: The process id to use.
        :param should_handle_data: Whether to handle data OR just print the conversation.
        :param temperature: The temperature to use.
        :param kwargs: Additional arguments.
        return: A new instance of a de-anonymiser.
        """
        self.process_handler = AMI_process_handler(process_id)

        # Accesses and keys
        langchain.debug = debug
        langchain.verbose = verbose
        keys = get_local_keys()
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = keys["huggingface_hub_token"]
        os.environ["OPENAI_API_KEY"] = keys["openai_api_key"]

        # Define the LLM and the conversation handler
        llm = load_model(temperature)
        self.conversation_handler = ConversationHandler(llm)
        
        self.should_handle_data = should_handle_data
        self.data_handler = DataHandler() if self.should_handle_data else None

        self.self_guide = self_guide
        self.google = load_google_search_tool() if google else None


    def re_identify(self, anon_text, file_name=None, **kwargs):
        """
        Re-identify a single text.
        :param anon_text: The anonymized text.
        """
        self.conversation_handler.start_conversation(self.process_handler.get_base_template())
        self.process_handler.new_process()
        response = ""
        
        for index, query in enumerate(self.process_handler):
            # For simplicity, we assume that the user input is currently only the anonymized text. 
            # Then, we send it to the conversation handler only with the first question.
            # We may update the user input to List if we want to support more than one input.
            user_input = anon_text if index == 0 else ""
            response = self.conversation_handler.send_new_message(query, user_input=user_input)
            print(f'Response: {response.get("data")}')
            if response.get('status') == ResponseStatus.ERROR:
                print("Error: response for file: ", file_name)
                if self.should_handle_data:
                    self.data_handler.add_error_file(file_name, response.get('data'))
                self.conversation_handler.end_conversation()
                break

            # update the process handler with the last response. So, it enables the process to decide whether to keep going or not. (based on the last response)
            self.process_handler.set_last_response(response.get('data')) 

            # currently, we support add_row only for one question.
            # TODO: support more than one question (add_row for all the questions of the process dataß)
            # for key, value in response.items():
            #     conv_responses_object[key] = value
        
        self.conversation_handler.end_conversation()

        if self.should_handle_data:
            conv_responses = self.process_handler.get_conv_responses()
            self.data_handler.add_flatten_row(conv_responses, file_name)
            
        
    def re_identify_list(self, study_dir_path, file_names, save_to_csv=False):        
        for i, file_name in enumerate(file_names):
            with open(
                os.path.join(study_dir_path, file_name), "r", encoding="utf-8"
            ) as f:
                anon_text = f.read()
            self.re_identify(anon_text, file_name)

    
    def get_results(self) -> pd.DataFrame:
        return self.data_handler.get_df() if self.should_handle_data else None
    
    def get_error_files(self) -> pd.DataFrame:
        return self.data_handler.get_error_files() if self.should_handle_data else None
