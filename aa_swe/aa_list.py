#!/usr/bin/env python3
import sys
from aa_swe.aa import aa_context, get_arg_range

def main():
    begin, end = get_arg_range()

    with aa_context() as aa:
        end = min(end, len(aa.lines))
        sys.stdout.write('\n')
        aa.display_lines(list(range(begin, end)), max_lines=None)
        sys.stdout.write('\n')


if __name__ == "__main__":
    main()
