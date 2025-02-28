#!/usr/bin/env python3
import sys
from pyflakes.api import check as pyflakes_check
from io import StringIO
from . import *

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

        new_lines = []
        new_lines.extend(aa.lines[:begin])
        new_begin = len(new_lines)
        body = sys.stdin.readlines()
        if len(body) > 0:
            if not body[-1].endswith('\n'):
                body[-1] = body[-1] + '\n'
        new_lines.extend(body)
        new_end = len(new_lines)
        new_lines.extend(aa.lines[end:])
        new_content = ''.join(new_lines)
        reporter = Reporter(new_lines)
        pyflakes_check(new_content, filename=aa.path, reporter=reporter)
        result = reporter.out.getvalue()
        if not result:
            with open(aa.path, "w") as f:
                f.write(new_content) 
            aa.set_path(aa.path)
            sys.stdout.write(f"{end-begin} lines replaced, new content:\n")
            lines= []
            stars = set()
            for i in range(max(0, new_begin - 5), new_begin):
                lines.append(i)
            for i in range(new_begin, new_end):
                lines.append(i)
                stars.add(i)
            for i in range(new_end, min(len(aa.lines), new_end + 5)):
                lines.append(i)
            aa.display_lines(lines, stars)
            sys.stdout.write("\nIf you don't like this, you need to revert with git.\n" )

        else:
            sys.stdout.write(f"Syntax errors found.  Not saving.\n")
            sys.stdout.write(result)
            return

if __name__ == "__main__":
    main()