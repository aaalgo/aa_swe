#!/usr/bin/env python3
import os
import sys
import json
from swebench.harness.test_spec.test_spec import make_test_spec
from swebench.harness.grading import get_eval_report, get_logs_eval, get_eval_tests_report, get_resolution_status
from swebench.harness.constants import (
    KEY_INSTANCE_ID,
    FAIL_TO_PASS,
    PASS_TO_PASS,
    FAIL_ONLY_REPOS,
    EvalType,
    ResolvedStatus,
)

def extract_first_exception(stdout_file):
    with open(stdout_file, 'r') as file:
        lines = file.readlines()
    for i in range(len(lines)):
        if lines[i].startswith("===========") and (i+1 < len(lines)):
            if not lines[i+1].startswith("ERROR:"):
                continue
            traceback_lines = [lines[i+1]]
            for j in range(i+3, len(lines)):
                if lines[j].startswith("----------------"):
                    break
                traceback_lines.append(lines[j])
            return traceback_lines
    return []

def print_error_details (traceback_lines, radius_before = 20, radius_after = 2):
    sys.stdout.write("First Exception Traceback:\n")
    for line in traceback_lines:
        sys.stdout.write(line + "\n")
    return
    sys.stdout.write("\nI have opened the errornous file for you:\n\n")
    error_path = None
    error_line = None
    error_function = None
    path_line_pattern = re.compile(r'File "(.+)", line (\d+), in (.+)')
    for line in traceback_lines:
        match = path_line_pattern.search(line)
        if match:
            error_path, error_line, error_function = match.groups()
            error_line = int(error_line) - 1
            break
    if not (error_path and error_line and error_function):
        return
    if not error_path.startswith("/testbed/"):
        return    
    error_path = "./" + error_path[len("/testbed/"):]    
    if not os.path.exists(error_path):
        return
    # error_function could be <module> or the function name
    with aa_context() as aa:
        aa.set_path(error_path)
        def_line = None      # find the line with def
        def_line_prefix = None
        for i, line in enumerate(aa.lines):
            if i >= error_line:
                break
            if not line.lstrip().startswith("def"):
                continue
            def_line_prefix = line[:(line.find("def") + 3)]
            if line[len(def_line_prefix):].lstrip().startswith(error_function):
                def_line = i
                break

        lines = []
        begin_line = error_line - radius_before
        end_line = min(error_line + radius_after + 1, len(aa.lines))
        if def_line is not None:
            lines.append(def_line)
            begin_line = max(begin_line, def_line + 1)
            begin_line = max(0, begin_line)

        for i in range(begin_line, end_line):
            lines.append(i)
            if def_line is not None:
                if aa.lines[i].startswith(def_line_prefix):
                    break
        aa.display_lines(lines, starred={error_line})
        sys.stdout.write("\n!!! Important: you are not allowed to modify the test cases.\n")

def main ():
    stdout_path = sys.argv[1]

    lines = extract_first_exception(stdout_path)
    if len(lines) > 0:
        print(' '.join(lines))
        return

    instance_dir = os.path.dirname(stdout_path)

    with open(os.path.join(instance_dir, "instance.json"), "r") as f:
        instance = json.load(f)
    spec = make_test_spec(instance)

    prediction = {
        'instance_id': spec.instance_id,
        'model_name_or_path': 'aaa',
        'model_patch': '',
    }
    report = get_eval_report(test_spec=spec, prediction=prediction, test_log_path=stdout_path, include_tests_status=True)
    eval_status_map, found = get_logs_eval(spec, stdout_path)
    if not found:
        return
    eval_type = EvalType.FAIL_ONLY if spec.repo in FAIL_ONLY_REPOS \
        else EvalType.PASS_AND_FAIL
    eval_ref = {
            KEY_INSTANCE_ID: spec.instance_id,
            FAIL_TO_PASS: spec.FAIL_TO_PASS,
            PASS_TO_PASS: spec.PASS_TO_PASS,
        }            
    report = get_eval_tests_report(
            eval_status_map, eval_ref, eval_type=eval_type
        )            
    if get_resolution_status(report) == ResolvedStatus.FULL.value:
        print("Congratulations! You have resolved the issue.")
    else:
        for name, key in [('You failed the following tests:', 'FAIL_TO_PASS'), ('You broke the following tests previously already passed:', 'PASS_TO_PASS')]:
            failed = report[key]['failure']
            if len(failed) == 0:
                continue
            print(name)
            for f in failed:
                print(f"\t{f}")