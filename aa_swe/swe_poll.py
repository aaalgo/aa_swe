import os
import glob
import json
import yaml

def main ():
    import argparse

    parser = argparse.ArgumentParser(description='Process poll results.')
    parser.add_argument('--update', action='store_true', help='Update the poll results')
    args = parser.parse_args()
    # Find all matching JSON files
    json_files = glob.glob('evaluation/lite/*/results/results.json')


    sols = []

    # Process each JSON file
    for json_file in json_files:
        root = os.path.dirname(os.path.dirname(json_file))
        with open(os.path.join(root, 'metadata.yaml'), 'r') as f:
            metadata = yaml.safe_load(f)
        if 'trajs' not in metadata:
            continue
        trajs = metadata['trajs']
        sol_name = os.path.basename(root)
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Extract instance_ids from the resolved list
                if 'resolved' in data:
                    c = len(data['resolved'])
                    sols.append((c, sol_name, trajs))
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    sols.sort(key=lambda x: x[0])
    for c, sol_name, trajs in sols:
        print(c, sol_name, trajs)
