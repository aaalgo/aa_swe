#!/usr/bin/env python3
import sys
import re
from collections import defaultdict
from aa_swe.aa import aa_context, get_arg_merged

def main():

    with aa_context() as aa:
        pattern = get_arg_merged('pattern')
        radius = 2
        max_lines = 25
        if not aa.lines:
            sys.stderr.write(f"Please aa_open a file before aa_search.\n")
            sys.stderr.write(f"In you want to search a directory, use the grep -r of Linux.\n")
            return 1
        try:
            regex = re.compile(pattern)
        except Exception as e:
            sys.stderr.write(f"Error compiling regex: {e}\n")
            return 1
        to_print = defaultdict(list)
        hits = 0
        for i, line in enumerate(aa.lines):
            if regex.search(line):
                hits += 1
                to_print[i].append(2)
                for j in range(i-radius, i+radius+1):
                    to_print[j].append(1)
        if hits == 0:
            sys.stdout.write(f"no matches found\n")
            return 0
        lines = []
        starred = set()
        for i, levels in to_print.items():
            if i < 0:
                continue
            if i >= len(aa.lines):
                continue
            lines.append(i)
            if max(levels) >= 2:
                starred.add(i)
        lines.sort()
        printed_hits = aa.display_lines(lines, starred, max_lines)   
        sys.stdout.write('\n')
        if printed_hits is not None and printed_hits < hits:
            sys.stdout.write(f'Found {hits} matches, first {printed_hits} displayed.\n')
        sys.stdout.write('Use aa_list to display more lines surrounding a hit.\n')

if __name__ == "__main__":
    main()