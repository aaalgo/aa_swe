#!/usr/bin/env python3
import os
import logging
import shutil
import json
from tqdm import tqdm
from datasets import load_dataset
import argparse
from swebench.harness.test_spec.test_spec import make_test_spec
import subprocess
import sys

ROOT=os.environ.get("AA_SWE_ROOT", None)
assert not ROOT is None, "Please set the AA_SWE_ROOT environment variable"

class Env:
    def __init__(self, instance, split):
        self.spec = make_test_spec(instance)
    #    spec fileds
    #        instance_id: str
    #        repo: str
    #        version: str
    #        repo_script_list: list[str]
    #        eval_script_list: list[str]
    #        env_script_list: list[str]
    #        arch: str
    #        FAIL_TO_PASS: list[str]
    #        PASS_TO_PASS: list[str]
    #        language: str
    #        docker_specs: dict
    #        namespace: str
    #        base_image_tag: str = LATEST
    #        env_image_tag: str = LATEST
    #        instance_image_tag: str = LATEST
        self.split = split
        self.base_commit = instance['base_commit']
        self.instance = instance
        self.work_dir = os.path.join(ROOT, 'insts', split, self.spec.instance_id)
        self.repo_dir = os.path.join(ROOT, "repos", self.spec.repo)

    def download_repo (self, force=False):
        if os.path.exists(os.path.join(self.repo_dir, "config")) and not force:
            logging.info(f"repo {self.spec.repo} already exists, not downloading")
            return
        os.makedirs(self.repo_dir, exist_ok=True)
        os.system(f'git clone --no-checkout --bare https://github.com/{self.spec.repo}.git {self.repo_dir}')

    def reset_work_dir (self, force=False):
        shutil.rmtree(self.work_dir, ignore_errors=True)
        #os.makedirs(self.work_dir, exist_ok=True)
        os.system(f'git clone --no-checkout --depth 1 {self.repo_dir} {self.work_dir}')
        os.system(f'cd {self.work_dir} && git fetch origin {self.base_commit}')
        os.system(f'cd {self.work_dir} && git checkout {self.base_commit}')
        os.makedirs(os.path.join(self.work_dir, ".swe"), exist_ok=True)
        with open(os.path.join(self.work_dir, ".swe", "instance.json"), "w") as f:
            json.dump(self.instance, f)
        with open(os.path.join(self.work_dir, ".swe", "problem_statement.txt"), "w") as f:
            f.write(self.instance['problem_statement'])
        eval_path = os.path.join(self.work_dir, ".swe", "eval.sh")
        with open(eval_path, "w") as f:
            f.write(self.spec.eval_script)
        os.system(f"chmod +x {eval_path}")


def checkout_main ():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--split', type=str, default='dev', help='The split to use (e.g., dev or test)')
    parser.add_argument('--instance', type=str, required=True, help='The instance ID to process')

    args = parser.parse_args()
    #FIELDS = ['instance_id', 'repo', 'version', 'install_repo_script', 'eval_script', 'setup_env_script', 'arch', 'base_image_key', 'env_dockerfile']
    swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split=args.split)
    instance = next((item for item in swebench if item['instance_id'] == args.instance), None)
    assert instance is not None, f"Instance {args.instance} not found in {args.split} split"
    env = Env(instance, split=args.split)
    env.reset_work_dir()

def list_main ():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--split', type=str, default='dev', help='The split to use (e.g., dev or test)')
    args = parser.parse_args()
    #FIELDS = ['instance_id', 'repo', 'version', 'install_repo_script', 'eval_script', 'setup_env_script', 'arch', 'base_image_key', 'env_dockerfile']
    swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split=args.split)
    for instance in swebench:
        print(instance['instance_id'])

def solve_main ():
    from glob import glob
    from mailcoach_lite import Engine, EmailMessage, Agent, ENQUEUE_MEMORY, ENQUEUE_TASK
    from mailcoach_lite.robots import Shell
    parser = argparse.ArgumentParser(description='Process an mbox file.')
    parser.add_argument('-s', '--solver', default='solver1.mbox', help='Path to solver memory.')
    parser.add_argument('--split', type=str, default=None, help='The split to use (e.g., dev or test)')
    parser.add_argument('-i', '--instance', type=str, required=True, help='The instance ID to process')
    parser.add_argument('-b', '--budget', type=float, default=1.0, help='The budget')
    args = parser.parse_args()
    split_pattern = args.split if args.split is not None else "*"
    paths = glob(os.path.join(ROOT, "insts", split_pattern, args.instance))
    if len(paths) == 0:
        print(f"No instances found for {args.instance}")
        return
    if len(paths) > 1:
        print(f"Multiple instances found for {args.instance}, please specify the split")
        return

    engine = Engine()
    engine.register(Shell("shell@localdomain"))
    pm_address = "user@localdomain"
    swe_address = "swe1@localdomain"
    engine.register(Agent(pm_address))
    engine.register(Agent(swe_address))
    engine.load_mbox(args.solver, ENQUEUE_MEMORY)

    os.chdir(paths[0])
    patch_link = os.path.join(".swe", "patch")
    if os.path.exists(patch_link):
        os.remove(patch_link)

    def stop_condition ():
        return os.path.exists(patch_link)

    os.system("pwd")
    message = EmailMessage()
    message["From"] = pm_address
    message["To"] = swe_address
    message["Subject"] = "New project"
    message.set_content(f"We are now in a new codebase.  Solve the issue as we did before.")
    engine.enqueue(message, ENQUEUE_TASK)
    engine.run(budget=args.budget, stop_condition=stop_condition)
    if os.path.exists(patch_link):
        logging.info(f"A patch was found; solver seems to have succeeded.")
    else:
        logging.info(f"No patch was found; solver has failed.")

if __name__ == "__main__":
    pass
