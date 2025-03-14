import sys
import os
import json
import re
from datetime import datetime
import subprocess
import logging
import argparse
from . import *

DEFAULT_TAG=os.environ.get("AA_SWE_TAG", "aa")

def docker_run (command, tag, interactive=False):
    if os.getenv('SWE_DEBUG'):
        logging.basicConfig(level=logging.DEBUG)
    # swe_run ...
    # will run the ... part in docker
    cwd = os.path.abspath(os.getcwd())
    with open(os.path.join(cwd, "..", "instance.json"), "r") as f:
        instance = json.load(f)
    eval_sh = os.path.abspath(os.path.join(cwd, "..", "eval.sh"))
    assert os.path.exists(eval_sh), f"eval.sh not found at {eval_sh}"
    docker_image = "sweb.eval.x86_64." + instance["instance_id"] + ":" + tag
    docker_instance = tag + "." + instance["instance_id"]
    # Check if the Docker instance exists
    result = subprocess.run(["docker", "ps", "-a", "--filter", f"name={docker_instance}", "--format", "{{.Names}}"], capture_output=True, text=True)
    existing_instance = result.stdout.strip()

    # Check the volume binding if the instance exists
    if existing_instance:
        logging.info(f"Docker instance {docker_instance} already exists, checking volume binding")
        result = subprocess.run(["docker", "inspect", "--format", "{{ range .Mounts }}{{ .Source }}:{{ .Destination }}{{ end }}", docker_instance], capture_output=True, text=True)
        bindings = result.stdout.strip()
        if True or f"{cwd}:/testbed" not in bindings:
            # Kill and remove the instance if the binding is incorrect
            logging.info(f"Binding is incorrect, removing instance {docker_instance}")
            subprocess.run(["docker", "kill", docker_instance])
            subprocess.run(["docker", "rm", "-f", docker_instance])
            existing_instance = None
        else:
            logging.info(f"Binding is correct, reusing instance")

    # Create the Docker instance if it doesn't exist or was removed
    #if not existing_instance or f"{cwd}:/testbed" not in bindings:
    #    logging.info(f"Creating new instance {docker_instance}")
    #    subprocess.run(["docker", "run", "-d", "--name", docker_instance, "-v", f"{cwd}:/testbed", "-v", f"{eval_sh}:/eval.sh", docker_image, "sleep", "infinity"])
    # Run the command inside the Docker container
    fake_git_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fake_git"))
    command0 = command
    command = ["docker", "run", "--rm", "-v", f"{cwd}:/testbed", "-v", f"{eval_sh}:/eval.sh", "-v", f"{fake_git_path}:/usr/bin/git"]
    if interactive:
        command.append("-it")
    command.append(docker_image)
    command.extend(command0)
    if interactive:
        result = subprocess.run(command)
    else:
        command_str = " ".join(command) + " 2>&1"
        logging.info(f"Running command: {command_str}")
        result = subprocess.run(command_str, shell=True, capture_output=True, text=True)
        return result

def run_main(tag="aa"):
    command = sys.argv[1:]
    docker_run(command, tag)


def extract_first_exception(stderr_file):
    with open(stderr_file, 'r') as file:
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


def test_main (tag=DEFAULT_TAG):
    parser = argparse.ArgumentParser(description='Run tests with optional interactive mode.')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
    args = parser.parse_args()

    if args.interactive:
        docker_run(["/bin/bash"], tag, interactive=True)
        return

    with aa_context() as aa:
        output_fname = f"stdout.{aa.trials}"
        aa.trials += 1
        stdout_path = os.path.join("..", output_fname)
        patch_path = os.path.join("..", "patch")
        fail_path = os.path.join("..", "failed")

        if True:    # run the test
            command = ["timeout", "300", "/eval.sh"]
            result = docker_run(command, tag)
            with open(stdout_path, "w") as f:
                f.write(result.stdout)
        
        error_lines = extract_first_exception(stdout_path)
        success = False
        if len(error_lines) == 0:
            if os.system(f"cd .. && swe_eval {output_fname} 2> /dev/null") == 0:
                success = True
                subprocess.run(f"git diff > {patch_path}", shell=True)
        else:
            print(''.join(error_lines))
        
        if not success:
            if aa.trials >= aa.max_trials:
                with open(fail_path, "w") as f:
                    f.write('failed test')
                    pass
        