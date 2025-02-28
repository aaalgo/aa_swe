#!/usr/bin/env python3
import sys
from . import aa_context

def main():

    with aa_context() as aa:
        aa.search(' '.join(sys.argv[1:]))

if __name__ == "__main__":
    main()