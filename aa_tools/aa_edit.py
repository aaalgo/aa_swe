#!/usr/bin/env python3
import sys
from . import *

def main():
    if len(sys.argv) < 2:
        sys.stderr.write('You must provide a range to edit, for example:\n')
        sys.stderr.write('aa_edit 32-48\n')
        return
    begin, end = parse_range(sys.argv[1])

    with aa_context() as aa:
        if aa.path is None:
            sys.stderr.write('You must open a file before editing it.\n')
            return
        top = aa.lines[:begin]
        bottom = aa.lines[end:]
        body = sys.stdin.read()
        with open(aa.path, "w") as f:
            f.writelines(top)
            f.write(body)
            if not body.endswith('\n'):
                f.write('\n')
            f.writelines(bottom)
        aa.set_path(aa.path)
        sys.stdout.write(f"{end-begin} lines replaced.\n")

if __name__ == "__main__":
    main()