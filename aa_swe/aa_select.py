import sys
from aa_swe.aa import aa_context, get_arg_range

def main ():
    begin, end = get_arg_range()
    with aa_context() as aa:
        if aa.path is None:
            sys.stderr.write('You must open a file before editing it.\n')
            return
        if 'test' in self.path:
            sys.stderr.write('You should not attempt to modify the test cases.')
            return
        sys.stdout.write('--- begin of selection ---\n')
        for i in range(begin, end):
            sys.stdout.write(aa.lines[i])
        sys.stdout.write('--- end of selection ---\n')
        sys.stdout.write('Check the above. If these are what you intend to modify proceed with aa_rewrite.  If the selected range is not correct, aa_select again or abandon.\n')
        aa.selection = [begin, end]
