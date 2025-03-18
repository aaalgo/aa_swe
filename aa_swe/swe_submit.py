#!/usr/bin/env python3
import sys
import os
from glob import glob
import json

def main():
    output_path = 'all_preds.jsonl'
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    cnt = 0
    with open(output_path, 'w') as f:
        for path in glob(os.path.join("*", "patch")):
            parent = os.path.dirname(path)
            instance_path = os.path.join(parent, "instance.json")
            with open(instance_path, 'r') as f2:
                instance = json.load(f2)
            instance_id = instance['instance_id']
            with open(path, 'r') as patch_file:
                patch = patch_file.read()
            if len(patch.strip()) == 0:
                print(f"{instance_id} is empty")
            out = {
                'instance_id': instance_id,
                'model_name_or_path': 'aaa',
                'model_patch': patch
            }
            f.write(json.dumps(out) + '\n')
            cnt += 1
    print(f"Wrote {cnt} ({cnt/300:.3f}) solutions to all_preds.jsonl")


if __name__ == "__main__":
    main()