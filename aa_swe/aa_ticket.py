#!/usr/bin/env python3
import os
import sys
import json

def main():
    if os.path.exists("./_aa_ticket"):
        os.system("cat ./_aa_ticket")
        return
    
    if not os.path.exists("/meta/instance.json"):
        sys.stderr.write("This is not a testbed directory.\n")
        sys.exit(1)
    with open("/meta/instance.json", "r") as f:
        instance = json.load(f)
    print(instance["problem_statement"])

if __name__ == "__main__":
    main()
