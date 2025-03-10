#!/usr/bin/env python3
import os
import json
import pkg_resources
from glob import glob
import pandas as pd

def scan_trace_and_log (solved):
    for path in glob("*/trace.mbox"):
        parent_path = os.path.dirname(path)
        with open(os.path.join(parent_path, "instance.json"), "r") as f:
            instance = json.load(f)
        instance_id = instance['instance_id']
        with open(path, "r") as f:
            text = f.read()
        off = text.find("New ticket:")
        if off < 0:
            continue
        if 'Congratulations!' in text[off:]:
            solved.add(instance_id)
            continue
        yield instance_id

    for path in glob("*/report.json"):
        instance_id = path.split("/")[0]
        with open(path, "r") as f:
            report = f.read()
        if '"resolved": false,' in report:
            yield instance_id
        else:
            solved.add(instance_id)

def main():
    survey_path = pkg_resources.resource_filename('aa_swe', 'data/survey.csv')
    survey = pd.read_csv(survey_path, dtype={'instance_id': str, 'solved': int})
    survey_dict = survey.set_index('instance_id')['solved'].to_dict()
    failed = []
    done = set()
    for instance_id in scan_trace_and_log(done):
        solved = survey_dict.get(instance_id, 0)
        failed.append((instance_id, solved))
    failed.sort(key=lambda x: x[1])
    for instance_id, solved in failed:
        if not instance_id in done:
            print(instance_id, solved)
    pass

if __name__ == "__main__":
    main()
