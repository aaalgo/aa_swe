#!/usr/bin/env python3
import os
import json
import subprocess as sp
import argparse
from swebench.harness.test_spec.test_spec import make_test_spec
from aa_swe.swe import load_instance, ROOT

def main():
    parser = argparse.ArgumentParser(description='Build docker image for a given instance')
    parser.add_argument('-i', '--instance', type=str, required=True, help='The instance ID to process')
    parser.add_argument('-f', '--force', action='store_true', help='Force rebuild of the docker image')
    args = parser.parse_args()

    image_name = f"aa_swe.{args.instance}"
    
    if not args.force:
        result = sp.run(f"docker image inspect {image_name}:latest >/dev/null 2>&1", shell=True)
        if result.returncode == 0:
            print(f"Docker image {image_name}:latest already exists. Use -f to force rebuild.")
            return

    work_dir = os.path.join(ROOT, 'docker', 'docker.' + args.instance)
    meta_dir = os.path.join(work_dir, "meta")
    testbed_dir = os.path.join(work_dir, "testbed")

    instance = load_instance(args.instance)
    assert instance is not None
    spec = make_test_spec(instance)
    os.makedirs(meta_dir, exist_ok=False)
    with open(os.path.join(meta_dir, "instance.json"), "w") as f:
        json.dump(instance, f)

    eval_path = os.path.join(meta_dir, "eval.sh")
    with open(eval_path, "w") as f:
        f.write(spec.eval_script)
    os.system(f"chmod +x {eval_path}")
    
    patched_setup_path = os.path.join(meta_dir, "patched_setup.sh")
    patched_eval_path = os.path.join(meta_dir, "patched_eval.sh")
    patched_script = spec.eval_script.replace("git ", "true ")
    # split the script into setup and eval with
    # the following separation pattern
    off = patched_script.find(">>>>> Start Test Output")
    assert off != -1
    test_offset = patched_script.rfind("\n", 0, off) + 1
    assert test_offset != 0
    with open(patched_setup_path, "w") as f:
        f.write(patched_script[:test_offset])
        f.write("/usr/bin/python3 -m pip install flask pyflakes\n")
    with open(patched_eval_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("set -uxo pipefail\n")
        #f.write("source /opt/miniconda3/bin/activate\n")
        #f.write("conda activate testbed\n")
        # we'll rely on the stub to load the anaconda environment
        f.write("cd /testbed\n")
        f.write(patched_script[test_offset:])
    os.system(f"chmod +x {patched_setup_path}")
    os.system(f"chmod +x {patched_eval_path}")

    with open(os.path.join(meta_dir, "test_patch"), "w") as f:
        f.write(instance['test_patch'])
    with open(os.path.join(meta_dir, "groundtruth"), "w") as f:
        f.write(instance['patch'])
    os.system(f'git clone --no-checkout {ROOT}/repos/{spec.repo} {testbed_dir}')
    os.system(f'cd {testbed_dir} && git checkout {instance["base_commit"]}')
    os.system(f'cd {testbed_dir} && git apply ../meta/test_patch && git commit -a -m test')
    with open(os.path.join(work_dir, "Dockerfile"), "w") as f:
        f.write(f"FROM sweb.eval.x86_64.{args.instance}:aa\n")
        f.write("COPY ./testbed /testbed\n")
        f.write("COPY ./meta /meta\n")
        f.write("RUN /meta/patched_setup.sh\n")
        f.write("WORKDIR /testbed\n")

    os.system(f"cd {work_dir}; docker build -t {image_name} .")