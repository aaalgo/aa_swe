#!/usr/bin/env python3
import sys
from aa_swe.aa import aa_context

def main():
    direction = 'down'
    if len(sys.argv) > 1:
        direction = sys.argv[1]

    with aa_context() as aa:
        last = aa.old_displayed_lines
        if last is None:
            sys.stdout.write('Cannot scroll.  Use aa_search or aa_list to display something first.\n')
            return 1
        if direction == 'down':
            begin = max(last) - 3
        else:
            begin = min(last) - 16
        end = begin + 20
        begin = max(0, begin)
        end = min(len(aa.lines), end)
        aa.display_lines(list(range(begin, end)), max_lines=None)

if __name__ == "__main__":
    main()
