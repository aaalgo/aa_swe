#!/usr/bin/env python3
import os
import sys
import json
from aa_swe.aa_swe import Env


def main ():
    current_directory = os.getcwd()
    parts = current_directory.rsplit('/', 2)
    assert len(parts) == 3, "Current directory structure is not as expected"
    _, split, instance_id = parts
    with open("instance.json", "r") as f:
        instance = json.load(f)
    env = Env(instance, split)
    env.eval(sys.argv[1])




