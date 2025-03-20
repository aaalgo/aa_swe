import os
import glob
import json
import yaml
import argparse
from glob import glob
import pkg_resources
import pandas as pd
from collections import Counter

ROOT=os.environ.get("AA_SWE_ROOT", None)
assert not ROOT is None, "Please set the AA_SWE_ROOT environment variable"

def main ():
    survey_path = pkg_resources.resource_filename('aa_swe', 'data/survey.csv')
    survey = pd.read_csv(survey_path, dtype={'instance_id': str, 'solved': int})
    survey_dict = survey.set_index('instance_id')['solved'].to_dict()
    #FIELDS = ['instance_id', 'repo', 'version', 'install_repo_script', 'eval_script', 'setup_env_script', 'arch', 'base_image_key', 'env_dockerfile']
    seen = set()
    solved = 0
    solved_test = 0
    failed = []
    with open('/data/aa/experiments/evaluation/lite/20250114_Isoform/results/results.json', 'r') as f:
        isoform = Counter(json.load(f)['resolved'])
    for path in glob(os.path.join("*", "patch")):
        parent_dir = os.path.dirname(path)
        with open(os.path.join(parent_dir, "instance.json"), "r") as f:
            instance = json.load(f)
        instance_id = instance['instance_id']
        split = instance['split']
        print("\033[92mSOLVED\033[0m", split, instance_id)
        if not (split, instance_id) in seen:
            seen.add((split, instance_id))
            solved += 1
            if split == 'test':
                solved_test += 1
    for path in glob(os.path.join("*", "failed")):
        parent_dir = os.path.dirname(path)
        with open(os.path.join(parent_dir, "instance.json"), "r") as f:
            instance = json.load(f)
        instance_id = instance['instance_id']
        split = instance['split']
        if not (split, instance_id) in seen:
            seen.add((split, instance_id))
            failed.append((isoform[instance_id], survey_dict.get(instance_id, 0), split, instance_id))
    failed.sort(key=lambda x: (x[0], x[1]))
    for iso, score, split, instance_id in failed:
        print("\033[91mFAILED\033[0m", split, instance_id, iso, score)
    
    todo = []
    for path in glob(os.path.join(ROOT, "insts", "*", "*")):
        _, split, instance_id = path.rsplit(os.sep, 2)
        if (split, instance_id) not in seen:
            trace = list(glob(instance_id + ".trace.*"))
            if len(trace) > 0:
                has_trace = "trace"
            else:
                has_trace = ""
            seen.add((split, instance_id))
            todo.append((isoform[instance_id], survey_dict.get(instance_id, 0), split, instance_id))
    todo.sort(key=lambda x: (x[0], x[1]))
    for iso, score, split, instance_id in todo:
        print("\033[93mUNSOLVED\033[0m", split, instance_id, iso, score)
    print(f"Solved: {solved}, Failed: {len(failed)}, Todo: {len(todo)}")
    print(f"Solved test: {solved_test}, {solved_test / 300:.3f}")