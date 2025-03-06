#!/usr/bin/env python3
import pkg_resources
from glob import glob
import pandas as pd

def main():
    survey_path = pkg_resources.resource_filename('aa_tools', 'data/survey.csv')
    survey = pd.read_csv(survey_path, dtype={'instance_id': str, 'solved': int})
    survey_dict = survey.set_index('instance_id')['solved'].to_dict()
    failed = []
    for path in glob("*.trace.20????????????"):
        instance_id, _ = path.split(".", 1)
        with open(path, "r") as f:
            text = f.readlines()
        bottom = ''.join(text[-10:])
        if 'Congratulations!' in bottom:
            continue
        solved = survey_dict.get(instance_id, 0)
        failed.append((instance_id, solved))
    failed.sort(key=lambda x: x[1])
    for instance_id, solved in failed:
        print(instance_id, solved)
    pass

if __name__ == "__main__":
    main()
