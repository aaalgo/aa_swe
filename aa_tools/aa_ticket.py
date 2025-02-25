#!/usr/bin/env python3
import os
import sys
import json


def main():
    if not os.path.exists(".swe"):
        sys.stderr.write("This is not a testbed directory.\n")
        sys.exit(1)
    with open(os.path.join(".swe", "instance.json"), "r") as f:
        instance = json.load(f)
    print(instance["problem_statement"])

if __name__ == "__main__":
    main()
