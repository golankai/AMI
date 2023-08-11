import os
import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

import torch as th
from torch.utils.data import DataLoader, Dataset

from transformers import TrainingArguments, RobertaForSequenceClassification

from clearml import Task


from utils import prepare_grader_data, compute_metrics

# Define constants
SUDY_NUMBER = 1
data_used = "famous_and_semi"
EXPERIMENT_NAME = f'eval_study_{SUDY_NUMBER}_{data_used}'

task = Task.init(project_name="AMI", task_name=EXPERIMENT_NAME, reuse_last_task_id=False, task_type=Task.TaskTypes.testing)

# Set up environment
trained_models_path = f"./anon_grader/trained_models/"
data_dir = f"textwash_data/study{SUDY_NUMBER}/intruder_test/full_data_study.csv"
PRED_PATH = "./anon_grader/results/predictions_" + data_used + ".csv"
RESULTS_PATH = "./anon_grader/results/results_" + data_used + ".csv"

DEVICE = "cuda" if th.cuda.is_available() else "cpu"

logging.info(f'Working on device: {DEVICE}')

# Cancel wandb logging
os.environ["WANDB_DISABLED"] = "true"


# Set seeds
SEED = 42
np.random.seed(SEED)
th.manual_seed(SEED)


# Read the data
columns_to_read = ["type", "text", "file_id", "name", "got_name_truth_q2"]
raw_data = pd.read_csv(data_dir, usecols=columns_to_read)

# Aggregate by file_id and calculate the rate of re-identification
data = (
    raw_data.groupby(["type", "file_id", "name", "text"])
    .agg({"got_name_truth_q2": "mean"})
    .reset_index()
)
data.rename(columns={"got_name_truth_q2": "human_rate"}, inplace=True)

# Define population to use
data = data[data["type"].isin(["famous", "semifamous"])]

# Preprocess the data
test_dataset = prepare_grader_data(data, SEED, DEVICE)['test']

# Create a DataLoader for the test dataset
test_dataloader = DataLoader(
    test_dataset,
    batch_size=64,
    shuffle=False,
)

models_names = os.listdir(trained_models_path)

# Predict with all models
for model_name in models_names:
    predictions = []

    # Load the model
    logging.info(f"Loading model from {model_name}")

    model_path = os.path.join(trained_models_path, model_name)
    model = RobertaForSequenceClassification.from_pretrained("roberta-base", num_labels=1).to(DEVICE)
    model.load_state_dict(th.load(model_path))
    model.eval()

    # Prediction
    for batch in test_dataloader:
        with th.no_grad():
            
            outputs = model(**batch)          
            regression_values = outputs["logits"].squeeze().cpu().tolist()
            
        predictions.extend(regression_values)
    print(f'Pred: {len(predictions)}')
    # Add predictions to the data
    print(len(data))
    data[f"model_{model_name}"] = predictions

data.to_csv(PRED_PATH)
task.upload_artifact("Predictions df", artifact_object=data)

# Calculate the overall mse for each model
results = {
    model_name: compute_metrics((data[model_name], data["human_rate"]))["mse"]
    for model_name in data.columns[7:]
}

# Save the results
results_df = pd.DataFrame.from_dict(results, orient="index", columns=["mse"])
results_df.to_csv(RESULTS_PATH)
task.upload_artifact("Results df", artifact_object=results_df)
