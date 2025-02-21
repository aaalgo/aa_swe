#!/usr/bin/env python3
from . import aa_context
import argparse

def main():
    with aa_context() as aa:
        aa.set_path(None)

if __name__ == "__main__":
    main()