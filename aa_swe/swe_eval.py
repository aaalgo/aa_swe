#!/usr/bin/env python3
import os
import sys
import json
from aa_swe.aa_swe import Env


def main ():
    with open("instance.json", "r") as f:
        instance = json.load(f)
    env = Env(instance["instance_id"])
    env.eval(sys.argv[1])




