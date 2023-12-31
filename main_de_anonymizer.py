import os
import random
from de_anonymizer.de_anonymizer import DeAnonymizer
from de_anonymizer.evaluation.experiment_evaluation import ExperimentEvaluation
from enum import Enum

from results.paths import ResultsPaths


class Mode(Enum):
    INTRUDER = 1
    EVALUATOR = 2

class ExperimentAnonTexts(Enum):
    ALL = 1
    ALL_OF_SELECTED_PERSONAS = 2
    SELECTED_LIST = 3
    SINGLE_TEXT = 4
    ALL_SEMI_FAMOUS = 5

############## --------------- Define the Mode --------------- ##############
mode = Mode.EVALUATOR
experimentMode = ExperimentAnonTexts.ALL

############## --------------- Define the Study, Process and Experiment properties --------------- ##############
study_number = 2
process_id = 5
experiment_number = 3
should_handle_data = True # handle dataFrame if True. Otherwise, just print the conversation.

############## --------------- For Selected Personas Experiment case --------------- ##############
personas_list = ["adele", "craig", "jagger"]

############## --------------- For Selected Texts Experiment case (one persona) --------------- ##############
persona_name = "adele" 
text_lists = [43, 47, 57, 61, 97, 112, 147]#, 157, 178, 197, 201, 209, 216, 242, 271, 287, 297, 302, 323, 357, 366, 377, 397, 423, 442, 468, 491, 497, 503, 547, 558, 576]

############## --------------- For Single Text Experiment case --------------- ##############
single_text_number = 576

result_type = "ami" # score
############## --------------- ----------------- --------------- ##############

texts_dir = f"textwash_data/study{study_number}/person_descriptions/anon"

result_base_path = f"results/{result_type}/study{study_number}/process{process_id}/experiment{experiment_number}"
if not os.path.exists(result_base_path):
    os.mkdir(result_base_path)


results_paths = ResultsPaths(
    raw=f"{result_base_path}/raw_results.csv",
    error_files_raw=f"{result_base_path}/raw_error_files.csv",
    processed=f"{result_base_path}/processed.csv",
    evaluation=f"{result_base_path}/evaluation.json",
)

# Preserve the same order of texts between experiments
random.seed(42)

def intruder():
    texts_file_names = []
    match experimentMode:
        case ExperimentAnonTexts.ALL:
            texts_file_names = os.listdir(texts_dir)
            random.shuffle(texts_file_names)
        case ExperimentAnonTexts.ALL_OF_SELECTED_PERSONAS:
            texts_file_names = [file_name for file_name in os.listdir(texts_dir) if file_name.split("_")[0] in personas_list]
            random.shuffle(texts_file_names)
        case ExperimentAnonTexts.SELECTED_LIST:
            texts_file_names = [f"{persona_name}_{text_number}.txt" for text_number in text_lists]
        case ExperimentAnonTexts.SINGLE_TEXT:
            texts_file_names = [f"{persona_name}_{single_text_number}.txt"]
        case ExperimentAnonTexts.ALL_SEMI_FAMOUS:
            texts_file_names = [file_name for file_name in os.listdir(texts_dir) if file_name.split("_")[0] == "semifamous"]

    de_anonymiser = DeAnonymizer(
        llm_name="chat-gpt", 
        process_id=process_id, 
        self_guide=True, 
        verbose=True, 
        should_handle_data=should_handle_data
    )

    
    de_anonymiser.re_identify_list(
        study_dir_path=texts_dir, 
        file_names=texts_file_names, 
        result_path=results_paths.raw,
        error_files_path=results_paths.error_files_raw
    )


def evaluator():
    result_analyzer = ExperimentEvaluation(results_paths=results_paths)
    result_analyzer.persona_successful_rate()
    result_analyzer.overall_successful_rate()
    result_analyzer.to_json()


if __name__ == "__main__":
    match mode:
        case Mode.INTRUDER:
            intruder()
        case Mode.EVALUATOR:
            evaluator()
