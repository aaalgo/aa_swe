import os
import sys
import json
import re
from io import StringIO
from collections import defaultdict
from contextlib import contextmanager

DEFAULT_WINDOW = 10

def get_arg_merged (name):
    if len(sys.argv) < 2:
        sys.stderr.write(f"usage: {os.path.basename(sys.argv[0])} <{name}>\n")
        sys.exit(1)
    return ' '.join(sys.argv[1:])

def get_arg_range ():
    range_ = "1"
    if len(sys.argv) > 1:
        range_ = ' '.join(sys.argv[1:])
    return parse_range(range_)

def parse_range(range_str, default_window=DEFAULT_WINDOW):
    """
    Parses a range string and returns a tuple representing the range.

    The input range string could be like "10" or "30-45".  The offsets
     in input are:
    - 1-based
    - right-inclusive

    The returned range is:
    - always a pair of (begin, end)
    - 0-based
    - right-exclusive

    Args:
        range_str: The range string to parse, in the format 'start-end' or simply 'start'.
        default_window (int, optional): The default window size to use if only a single number is provided. Defaults to DEFAULT_WINDOW.

    Returns:
        tuple: A tuple (begin, end) representing the parsed range.
    """
    try:
        range = [int(x.strip()) for x in range_str.split('-')]
        assert len(range) == 1 or len(range) == 2
    except:
        sys.stderr.write(f"Invalid range: {range_str}\n")
        sys.stderr.write("Range must be one of the following:\n")
        sys.stderr.write("  N: e.g. 10\n")
        sys.stderr.write("  M-N: e.g. 30-45\n")
        sys.exit(1)

    if len(range) == 1:
        begin = range[0] - 1
        end = range[0]
        if default_window is not None:
            end = begin + default_window
        return begin, end
    return range[0] - 1, range[1]

class Context:
    def __init__ (self, state_dir):
        self.root = state_dir
        self.state_path = os.path.join(self.root, 'state.json')
        self.path = None                    # path to the open file
        self.lines = []                     # lines of the open file
                                            # upon failure of which will
                                            # give up and exit
        self.displayed_lines = None         # lines displayed last time
        self.old_displayed_lines = None     # lines displayed before that
        self.selection = None               # current selection
        self.old_selection = None           # selection before last display
        # - the range of displayed lines is kept for til the next command
        # so aa_scrow can work
        # - the selection is kept for til the next command
        # so aa_rewrite can work
        assert os.path.exists(self.root), f"state directory not found: {self.root}"

        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                try:
                    state = json.load(f)
                    self.set_path(state['path'])
                    self.old_displayed_lines = state.get('old_displayed_lines', None)
                    self.old_selection = state.get('old_selection', None)
                except Exception as e:
                    pass

    def save (self):
        with open(self.state_path, 'w') as f:
            json.dump({
                'path': self.path,
                'old_displayed_lines': self.displayed_lines,
                'old_selection': self.selection
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
        self.old_displayed_lines = None
        with open(path, "r") as f:
            self.lines = f.readlines()

    def display_state (self):
        if self.lines:
            sys.stdout.write(f"current file: {self.path}\n")
            sys.stdout.write(f"total lines: {len(self.lines)}\n")
            if self.selection is None:
                if self.displayed_lines is None:
                    sys.stdout.write(f"cannot scroll\n")
                else:
                    first = min(self.displayed_lines)
                    last = max(self.displayed_lines)
                    if first == 0 and last == len(self.lines) - 1:
                        sys.stdout.write(f"cannot scroll\n")
                    elif first == 0:
                        sys.stdout.write(f"can scroll down\n")
                    elif last == len(self.lines) - 1:
                        sys.stdout.write(f"can scroll up\n")
                    else:
                        sys.stdout.write(f"can scroll\n")
            else:
                sys.stdout.write(f"selection for rewrite: {self.selection[0]+1}-{self.selection[1]}\n")
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


@contextmanager
def aa_context():
    """
    Context manager for managing shared global state.

    Usage:
        with aa_context() as aa:
            ... modify aa ...
    """
    # Load state if exists, otherwise start with empty dict
    AA_SWE_WORK_DIR = os.getenv('AA_SWE_WORK_DIR', './')
    aa = Context(AA_SWE_WORK_DIR)
    try:
        yield aa  # Provide the state to the user
    finally:
        # Save the updated state back to STATE_PATH
        aa.display_state()
        aa.save()

class Reporter:

    def __init__ (self, lines):
        self.out = StringIO()
        self.lines = lines

    def unexpectedError(self, filename, msg):
        #self.out.write(f"{filename}: {msg}\n")
        pass

    def syntaxError(self, filename, msg, lineno, offset, text):
        if text is None:
            line = None
        else:
            line = text.splitlines()[-1]
        lineno = max(lineno or 0, 1)

        if offset is not None:
            # some versions of python emit an offset of -1 for certain encoding errors
            offset = max(offset, 1)
            self.out.write('%s:%d:%d: %s\n' %
                               (filename, lineno, offset, msg))
        else:
            self.out.write('%s:%d: %s\n' % (filename, lineno, msg))

        if line is None:
            return
        
        line = line + '\n'
        lineno -= 1
        if lineno >= 0 and (line == self.lines[lineno]):
            begin = max(lineno-2, 0)
            end = min(lineno+4, len(self.lines))
            margin = len(str(end))
            for i in range(begin, end):
                star = "*" if i == lineno else " "
                self.out.write(f"{star}{i+1:>{margin}}: {self.lines[i]}")
                if i == lineno and offset is not None:
                    self.out.write(' ' * (2 + margin + offset) + "^\n")
                self.out.write('\n')

    def flake(self, message):
        return
        if 'imported but unused' in msg:
            return
        self.out.write(str(message))
        self.out.write('\n')
