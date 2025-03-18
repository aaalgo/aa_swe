#!/usr/bin/env python3
import os
import pickle

ROOT=os.environ.get("AA_SWE_ROOT", None)
assert not ROOT is None, "Please set the AA_SWE_ROOT environment variable"

def load_instance (instance_id):
    with open(os.path.join(ROOT, "datasets.pkl"), "rb") as f:
        datasets = pickle.load(f)
    split = None
    instance = None
    for sp, dataset in datasets.items():
        instance = dataset.get(instance_id, None)
        if instance is not None:
            split = sp
            break
    assert instance is not None, f"Instance {instance_id} not found in any split"
    instance['split'] = split
    return instance

class Env:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.split = split
        instance['split'] = split
        assert self.instance_id == instance['instance_id'], f"Instance ID mismatch: {self.instance_id} != {instance['instance_id']}"
        self.instance = instance
        self.base_commit = instance['base_commit']
