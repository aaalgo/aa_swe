#!/usr/bin/env python3
from . import aa_context
import argparse

def main():
    parser = argparse.ArgumentParser(description='Open a file and manage its state.')
    parser.add_argument('pattern', type=str, help='The pattern to search for')
    args = parser.parse_args()

    with aa_context() as aa:
        aa.search(args.pattern)

if __name__ == "__main__":
    main()