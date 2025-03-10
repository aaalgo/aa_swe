import os
import sys
import json
import re
from collections import defaultdict
from contextlib import contextmanager


def parse_range (range, default_window=None):
    range = [int(x.strip()) for x in range.split('-')]
    if len(range) == 1:
        begin = range[0] - 1
        end = range[0]
        if default_window is not None:
            end = begin + default_window
        return begin, end
    return range[0]-1, range[1]

DEFAULT_MAX_TRIALS = 5

class Context:
    def __init__ (self, state_path):
        self.path = None
        self.lines = []
        self.trials = 0
        self.max_trials = DEFAULT_MAX_TRIALS
        self.displayed_lines = None
        self.last_displayed_lines = None
        self.old_selection = None
        self.selection = None
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                try:
                    state = json.load(f)
                    self.set_path(state['path'])
                    self.last_displayed_lines = state.get('last_displayed_lines', None)
                    self.trials = state.get('trials', 0)
                    self.max_trials = state.get('max_trials', DEFAULT_MAX_TRIALS)
                    self.old_selection = state.get('selection', None)
                except Exception as e:
                    pass

    def save (self, state_path):
        with open(state_path, 'w') as f:
            json.dump({
                'path': self.path,
                'last_displayed_lines': self.displayed_lines,
                'trials': self.trials,
                'max_trials': self.max_trials,
                'selection': self.selection
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
        self.last_displayed_lines = None
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
            if self.selection is not None:
                sys.stdout.write(f"selection: {self.selection[0]+1}-{self.selection[1]}\n")
        else:
            sys.stdout.write(f"no file loaded\n")

    def summary (self):
        if not self.path.endswith('.py'):
            return
        defs = [] # i, offset
        min_off = 1000000
        for i, line in enumerate(self.lines):
            off = line.find('def ')
            if off < 0:
                continue
            if line[:off].strip() != "":
                continue
            defs.append((i, off))
            min_off = min(min_off, off)
        lines = []
        stars = set()
        for i, off in defs:
            if off > min_off:
                continue
            lines.append(i)
            stars.add(i)
            line = self.lines[i]
            if '(' in line:
                i0 = i
                while not ')' in line and i < i0 + 2:
                    i += 1
                    if i >= len(self.lines):
                        break
                    lines.append(i)
                    line += self.lines[i]
        if len(lines) > 0:
            if len(stars) > 20:
                sys.stdout.write(f"Too many def lines, not displaying.\n")
                return
            sys.stdout.write(f"def lines:\n\n")
            hits = self.display_lines(lines, stars, max_lines=100)
            sys.stdout.write('\n')
            if hits is not None and hits < len(stars):
                sys.stdout.write(f'{len(stars) - hits} more def not displayed.')
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
            if i < 0:
                continue
            if i >= len(self.lines):
                continue
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
        sys.stdout.write('\n')

    def search (self, pattern, radius=2, max_lines=25):
        if not self.lines:
            sys.stderr.write(f"No file loaded. Please aa_open a file first.\n")
            sys.stderr.write(f"In you want to search a directory, use grep instead.\n")
            return
        try:
            regex = re.compile(pattern)
        except Exception as e:
            sys.stderr.write(f"Error compiling regex: {e}\n")
            return
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
        sys.stdout.write('\n')
        if printed_hits is not None and printed_hits < hits:
            sys.stdout.write(f'Found {hits} matches, first {printed_hits} displayed.\n')
        sys.stdout.write('Use aa_list to display more lines surrounding a hit.\n')

@contextmanager
def aa_context():
    """
    Context manager for managing shared global state.

    Usage:
        with aa_context() as aa:
            ... modify aa ...
    """
    # Load state if exists, otherwise start with empty dict
    AA_SWE_WORK_DIR = os.getenv('AA_SWE_WORK_DIR')
    assert AA_SWE_WORK_DIR is not None, "AA_SWE_WORK_DIR is not set"
    state_path = os.path.join(AA_SWE_WORK_DIR, 'state.json')
    aa = Context(state_path)
    try:
        yield aa  # Provide the state to the user
    finally:
        # Save the updated state back to STATE_PATH
        aa.display_state()
        aa.save(state_path)
