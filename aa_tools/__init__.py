import os
import sys
import json
import re
from collections import defaultdict
from contextlib import contextmanager

STATE_PATH = os.path.expanduser('~/.aa_state')

def parse_range (range, default_window=None):
    range = [int(x.strip()) for x in range.split('-')]
    if len(range) == 1:
        begin = range[0] - 1
        end = range[0]
        if default_window is not None:
            end = begin + default_window
        return begin, end
    return range[0]-1, range[1]

class Context:
    def __init__ (self, state_path):
        self.path = None
        self.lines = []
        self.displayed_lines = None
        self.last_displayed_lines = None
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = json.load(f)
                self.set_path(state['path'])
                self.last_displayed_lines = state.get('last_displayed_lines', None)

    def save (self, state_path):
        with open(state_path, 'w') as f:
            json.dump({
                'path': self.path,
                'last_displayed_lines': self.displayed_lines
            }, f)

    def set_path (self, path):
        if path is None:
            self.path = None
            self.lines = []
            return
        if not os.path.exists(path):
            sys.stderr.write(f"file not found: {path}\n")
            return
        self.path = path
        self.lines = []
        with open(path, "r") as f:
            self.lines = f.readlines()

    def display_state (self):
        if self.lines:
            sys.stdout.write(f"current file: {self.path}\n")
            sys.stdout.write(f"total lines: {len(self.lines)}\n")
            if self.displayed_lines is None:
                sys.stdout.write(f"cannot scroll\n")
            else:
                sys.stdout.write(f"can scroll\n")
        else:
            sys.stdout.write(f"no file loaded\n")

    def summary (self):
        pass

    def print_window (self, line = None, window=10, suffix=True, star=None):
        l = line - 1
        begin = max(0, l)
        end = min(len(self.lines), l + window)
        to_append = []
        leading_width = 0
        for i in range(begin, end):
            leading = '*' if i + 1 == star else ''
            to_append.append((leading + str(i+1), self.lines[i].rstrip()))
            leading_width = max(leading_width, len(to_append[-1][0]))
        for leading, line in to_append:
            sys.stdout.write(f'{leading:>{leading_width}}|{line}\n')

        remain = len(self.lines) - end
        if remain > 0 and suffix:
            sys.stdout.write('')
            sys.stdout.write(f'{len(self.lines) - end} more lines below.\n')

    def display_lines (self, lines, starred = set(), max_lines = 25):
        if len(lines) == 0:
            self.displayed_lines = None
            return
        self.displayed_lines = lines
        margin = max(3, len(str(lines[-1]+1)))
        printed_hits = 0
        printed_lines = 0
        last = None
        for i in lines:
            if max_lines is not None and printed_lines >= max_lines:
                break
            if last is not None and last + 1 < i:
                sys.stdout.write(' ')
                sys.stdout.write('.'* margin)
                sys.stdout.write('|\n')
            last = i
            mark = ' '
            if i in starred:
                mark = '*'
                printed_hits += 1
            sys.stdout.write(f'{mark}{i+1:>{margin}}|{self.lines[i].rstrip()}\n')
            printed_lines += 1
        return printed_hits

    def view (self, begin, end):
        end = min(end, len(self.lines))
        self.display_lines(list(range(begin, end)), max_lines=None)

    def search (self, pattern, radius=2, max_lines=25):
        if not self.lines:
            return
        regex = re.compile(pattern)
        to_print = defaultdict(list)
        hits = 0
        for i, line in enumerate(self.lines):
            if regex.search(line):
                hits += 1
                to_print[i].append(2)
                for j in range(i-radius, i+radius+1):
                    to_print[j].append(1)
        if hits == 0:
            sys.stdout.write(f"no matches found\n")
            return
        lines = []
        starred = set()
        for i, levels in to_print.items():
            if i < 0:
                continue
            if i >= len(self.lines):
                continue
            lines.append(i)
            if max(levels) >= 2:
                starred.add(i)
        lines.sort()
        printed_hits = self.display_lines(lines, starred, max_lines)   
        if printed_hits < hits:
            sys.stdout.write(f'Found {hits} matches, first {printed_hits} displayed.\n')
        sys.stdout.write('Use aa_view to display more lines surrounding a hit.\n')

@contextmanager
def aa_context(state_path=STATE_PATH):
    """
    Context manager for managing shared global state.

    Usage:
        with aa_context() as aa:
            ... modify aa ...
    """
    # Load state if exists, otherwise start with empty dict
    aa = Context(state_path)
    try:
        yield aa  # Provide the state to the user
    finally:
        # Save the updated state back to STATE_PATH
        aa.display_state()
        aa.save(state_path)
