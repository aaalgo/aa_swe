#!/usr/bin/env python3
import os, sys
from aa_swe.aa import aa_context, get_arg_merged

def main():
    path = get_arg_merged('path')

    with aa_context() as aa:
        if os.path.exists(path):
            sys.stderr.write(f"file already exists: {path}\n")
            return 1
        aa.set_path(None)
        if '/' in path:
            dir_ = os.path.dirname(path)
            os.makedirs(dir_, exist_ok=True)
        with open(path, "w") as f:
            for line in sys.stdin:
                f.write(line)
        sys.stdout.write(f"created file: {path}\n")

if __name__ == "__main__":
    main()