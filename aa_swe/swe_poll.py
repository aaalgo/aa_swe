import glob
import json
from collections import Counter
import pkg_resources
import pandas as pd

def main ():
    import argparse

    parser = argparse.ArgumentParser(description='Process poll results.')
    parser.add_argument('--update', action='store_true', help='Update the poll results')
    args = parser.parse_args()
    # Find all matching JSON files
    json_files = glob.glob('evaluation/lite/*/results/results.json')

    # Counter to track instance_id occurrences
    instance_counts = Counter()

    # Process each JSON file
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Extract instance_ids from the resolved list
                if 'resolved' in data:
                    for instance_id in data['resolved']:
                        instance_counts[instance_id] += 1
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

    # Sort and print results by count
    for instance_id, count in sorted(instance_counts.items(), key=lambda x: x[1]):
        print(f"{instance_id}\t{count}")
    survey_path = pkg_resources.resource_filename('aa_swe', 'data/survey.csv')
    if args.update:
        # Convert instance_counts to a DataFrame
        df = pd.DataFrame(list(instance_counts.items()), columns=['instance_id', 'solved'])
        df.to_csv(survey_path, index=False)

