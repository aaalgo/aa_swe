#!/usr/bin/env python3
import sys
from . import *

def main():
    range_ = "1"
    if len(sys.argv) > 1:
        range_ = sys.argv[1]

    begin, end = parse_range(range_, 20)

    with aa_context() as aa:
        sys.stdout.write('\n')
        aa.view(begin, end)

if __name__ == "__main__":
    main()
