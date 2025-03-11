#!/usr/bin/env python3
import sys
from . import *

def main():
    direction = 'down'
    if len(sys.argv) > 1:
        direction = sys.argv[1]

    with aa_context() as aa:
        last = aa.last_displayed_lines
        if last is None:
            sys.stdout.write('Cannot scroll.  Use aa_search or aa_list to display something first.\n')
            return
        if direction == 'down':
            begin = max(last) - 3
        else:
            begin = min(last) - 16
        end = begin + 20
        aa.view(max(0, begin), min(len(aa.lines), end))

if __name__ == "__main__":
    main()
