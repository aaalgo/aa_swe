import os
import sys
import pickle
from aa_swe.aa import aa_context, get_arg_merged

def find_def_or_class (kind):
    name = get_arg_merged("name")
    with aa_context() as aa:
        index = pickle.load(open(os.path.join(aa.root, "index.pkl"), "rb"))
        hits = index[kind].get(name, [])
        if len(hits) == 0:
            sys.stderr.write(f"Nothing found for {kind} {name}; try using grep.\n")
            return
        for path, begin, end in hits:
            print(path)
            aa.set_path(path)
            aa.display_lines(list(range(begin, begin+1)))
        aa.set_path(None)

def main ():
    find_def_or_class('def')