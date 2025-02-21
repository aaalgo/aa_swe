#!/usr/bin/env python3
import os, sys
from . import aa_context
import argparse

def main():
    parser = argparse.ArgumentParser(description='Open a file and manage its state.')
    parser.add_argument('path', type=str, help='The path to the file to open')
    args = parser.parse_args()

    with aa_context() as aa:
        aa.set_path(None)
        if os.path.exists(args.path):
            sys.stderr.write(f"file already exists: {args.path}\n")
            return
        if '/' in args.path:
            dir_ = os.path.dirname(args.path)
            os.makedirs(dir_, exist_ok=True)
        with open(args.path, "w") as f:
            for line in sys.stdin:
                f.write(line)
        aa.set_path(args.path)

if __name__ == "__main__":
    main()