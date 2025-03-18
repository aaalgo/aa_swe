import os
import ast
import pickle
from collections import defaultdict
from aa_swe.aa import aa_context

# This program initialize the internal part of an aa_swe session.
# It indexes all source code for defs.

def create_source_index():
    def_index = defaultdict(list)
    class_index = defaultdict(list)
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    file_content = f.read()
                    try:
                        tree = ast.parse(file_content, filename=path)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                def_name = node.name
                                end_lineno = node.body[-1].lineno if node.body else node.lineno
                                def_index[def_name].append((path, node.lineno - 1, end_lineno))
                            elif isinstance(node, ast.ClassDef):
                                class_name = node.name
                                end_lineno = node.body[-1].lineno if node.body else node.lineno
                                class_index[class_name].append((path, node.lineno - 1, end_lineno))
                    except:
                        lines = file_content.split('\n')
                        for i, line in enumerate(lines):
                            off = line.find('def ')
                            if off != -1:
                                def_name = line[off+4:].split('(')[0].strip()
                                def_index[def_name].append((path, i, None))
                            off = line.find('class ')
                            if off != -1:
                                rest = line[off+6:]
                                offset1 = rest.find('(')
                                offset2 = rest.find(':')
                                if offset1 < 0:
                                    offset = offset2
                                elif offset2 < 0:
                                    offset = offset1
                                else:
                                    offset = min(offset1, offset2)
                                if offset >= 0:
                                    class_name = rest[:offset].strip()
                                    class_index[class_name].append((path, i, None))
    return {'def': def_index, 'class': class_index}

def main ():
    with aa_context() as aa:
        testbed = '/testbed'
        assert os.path.exists(testbed)
        os.chdir(testbed)
        index = create_source_index()
        with open(os.path.join(aa.root, "index.pkl"), "wb") as f:
            pickle.dump(index, f)
        aa.set_path(None)

