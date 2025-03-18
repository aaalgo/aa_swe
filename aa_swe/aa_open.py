#!/usr/bin/env python3
import os
import sys
from aa_swe.aa import aa_context, get_arg_merged

def main():
    path = get_arg_merged('path')

    with aa_context() as aa:
        if not os.path.isfile(path):
            sys.stderr.write(f"Error: {path} is not a valid file or does not exist.\n")
            return 1
        aa.set_path(path)
        aa.summary()

if __name__ == "__main__":
    main()