#!/usr/bin/env python3
import os
import sys
from . import aa_context
import argparse

def main():
    parser = argparse.ArgumentParser(description='Open a file and manage its state.')
    parser.add_argument('path', type=str, help='The path to the file to open')
    args = parser.parse_args()

    with aa_context() as aa:
        if not os.path.isfile(args.path):
            sys.stderr.write(f"Error: {args.path} is not a valid file or does not exist.\n")
            return
        aa.set_path(args.path)
        aa.summary()

if __name__ == "__main__":
    main()