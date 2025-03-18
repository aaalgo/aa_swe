#!/usr/bin/env python3
import sys
from pyflakes.api import check as pyflakes_check
from aa_swe.aa import aa_context, Reporter

def main ():
    with aa_context() as aa:
        if aa.path is None:
            sys.stderr.write('You must open a file before editing it.\n')
            return
        if aa.old_selection is None:
            sys.stderr.write('You must select a range before replacing it.\n')
            return
        begin, end = aa.old_selection
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
        result = None
        if aa.path.endswith('.py'):
            reporter = Reporter(new_lines)
            pyflakes_check(new_content, filename=aa.path, reporter=reporter)
            result = reporter.out.getvalue()
        if not result:
            with open(aa.path, "w") as f:
                f.write(new_content) 
            aa.set_path(aa.path)
            sys.stdout.write(f"{end-begin} lines rewritten, new content:\n")
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
            if "```" in ''.join(body):
                sys.stdout.write("Not not quote your code with ```.  Your email body should contain only the rewritten lines.\n")
            else:
                sys.stdout.write(f"Syntax errors found.  Not saving.\n")
                sys.stdout.write(result)
                if len(body) > 10:
                    sys.stdout.write("Try select fewer lines for modification.")
            return

