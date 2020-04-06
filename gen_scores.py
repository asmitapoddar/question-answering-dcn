from constants import *
import os
from pathlib import Path
import subprocess
import sys
import torch as th
    
FREQ = 10  # Evals every 10th model. With save frequency = 10 batches, it evals every 10*10=100 batches.
TEMP_JSON_FILENAME = "kuba_temp.json"

def gen_predictions(model_path, dataset_path)
    tokenized_dataset_path = dataset_path.split(".")[0]+"-tokenized.json"
    subprocess.run(["python3", "produce_answers.py", model_path, tokenized_dataset_path, TEMP_JSON_FILENAME])

def run_eval(dataset_path)
    p = subprocess.run(["python3", "evaluate-v2.0.py", dataset_path, TEMP_JSON_FILENAME], check=True, stdout=subprocess.PIPE, universal_newlines=True)
    outp = p.stdout
    em_score = outp.split('"exact": ')[1].split(",")[0]
    f1_score = outp.split('"f1": ')[1].split(",")[0]
    total = outp.split('"total": ')[1].split(",")[0]
    return em_score, f1_score, total

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print()
    else:
        model_dir = sys.argv[1]
        if model_dir[-1] != '/':
            model_dir += '/'
        dataset_path = sys.argv[2]

        with open(model_dir+"scores.log", "w") as scores_file:
            paths = sorted(Path(dirpath).iterdir(), key=os.path.getmtime)
            for i, model_path in enumerate(paths):
                if i % FREQ != 0:
                    continue
                if ".par" not in model_path:
                    continue
                print("Evaluating model: '%s' ..." % model_path, end='')
                global_step = th.load(model_path)[SERIALISATION_KEY_GLOBAL_STEP]
                gen_predictions(model_path, dataset_path)
                em_score, f1_score, total = run_eval(dataset_path)
                scores_file.write(global_step + "," + em_score + "," + f1_score + "," + total + "\n")
                print(" done.")
