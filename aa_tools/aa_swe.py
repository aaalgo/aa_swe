#!/usr/bin/env python3
import sys
import os
import logging
import shutil
import json
import subprocess
from glob import glob
from datetime import datetime
from tqdm import tqdm
from datasets import load_dataset
import argparse
from swebench.harness.test_spec.test_spec import make_test_spec
from . import aa_context

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
        os.system(f'git clone --no-checkout --depth 1 {self.repo_dir} {self.work_dir}/testbed')
        os.system(f'cd {self.work_dir}/testbed && git fetch origin {self.base_commit}')
        os.system(f'cd {self.work_dir}/testbed && git checkout {self.base_commit}')
        with open(os.path.join(self.work_dir, "instance.json"), "w") as f:
            json.dump(self.instance, f)
        with open(os.path.join(self.work_dir, "problem_statement.txt"), "w") as f:
            f.write(self.instance['problem_statement'])
        eval_path = os.path.join(self.work_dir, "eval.sh")
        with open(eval_path, "w") as f:
            f.write(self.spec.eval_script)
        os.system(f"chmod +x {eval_path}")

def download_main ():
    for split in ['dev', 'test']:
        swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split=split)
        for instance in swebench:
            env = Env(instance, split=split)
            env.download_repo()


def checkout_main ():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--split', type=str, default=None, help='The split to use (e.g., dev or test)')
    parser.add_argument('--instance', type=str, required=True, help='The instance ID to process')

    args = parser.parse_args()
    splits = ['dev', 'test']
    if args.split is not None:
        splits = [args.split]
    for split in splits:
        swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split=split)
        instance = next((item for item in swebench if item['instance_id'] == args.instance), None)
        if not instance is None:
            env = Env(instance, split=split)
            env.reset_work_dir()
            break
    assert instance is not None, f"Instance {instance} not found in any split"

def list_main ():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--split', type=str, default='dev', help='The split to use (e.g., dev or test)')
    args = parser.parse_args()
    #FIELDS = ['instance_id', 'repo', 'version', 'install_repo_script', 'eval_script', 'setup_env_script', 'arch', 'base_image_key', 'env_dockerfile']
    seen = set()
    solved = 0
    failed = 0
    for path in glob(os.path.join(ROOT, "insts", "*", "*", "patch")):
        _, split, instance_id, _ = path.rsplit(os.sep, 3)
        print("\033[92mSOLVED\033[0m", split, instance_id)
        seen.add((split, instance_id))
        solved += 1
    for path in glob(os.path.join(ROOT, "insts", "*", "*", "failed")):
        _, split, instance_id, _ = path.rsplit(os.sep, 3)
        with open(path, "r") as f:  
            failed_reason = f.read().strip()
        if len(failed_reason) == 0:
            failed_reason = "failed test"
        trace = list(glob(instance_id + ".trace.*"))
        if len(trace) > 0:
            has_trace = "trace"
        else:
            has_trace = ""
        print("\033[91mFAILED\033[0m", split, instance_id, failed_reason, has_trace)
        seen.add((split, instance_id))
        failed += 1
    
    for path in glob(os.path.join(ROOT, "insts", "*", "*")):
        _, split, instance_id = path.rsplit(os.sep, 2)
        if (split, instance_id) not in seen:
            trace = list(glob(instance_id + ".trace.*"))
            if len(trace) > 0:
                has_trace = "trace"
            else:
                has_trace = ""
            print("\033[93mUNSOLVED\033[0m", split, instance_id, has_trace)
            failed += 1
    print(f"Solved: {solved}, Failed: {failed}")

def solve_main ():
    from glob import glob
    from mailcoach_lite import Engine, EmailMessage, Agent, ENQUEUE_MEMORY, ENQUEUE_TASK, DEFAULT_MODEL
    from mailcoach_lite.robots import Shell
    parser = argparse.ArgumentParser(description='Process an mbox file.')
    parser.add_argument('-s', '--solver', default='solver1.mbox', help='Path to solver memory.')
    parser.add_argument('--split', type=str, default=None, help='The split to use (e.g., dev or test)')
    parser.add_argument('-i', '--instance', type=str, required=True, help='The instance ID to process')
    parser.add_argument('-b', '--budget', type=float, default=0.1, help='The budget')
    parser.add_argument('-m', '--model', default='openai/gpt-4o-mini', help='The model to use.')
    parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
    parser.add_argument('-f', '--force', action='store_true', help='Force the operation to run even if conditions are not met')
    parser.add_argument('--max_trials', type=int, default=8, help='The maximum number of trials allowed')
    args = parser.parse_args()
    split_pattern = args.split if args.split is not None else "*"
    paths = glob(os.path.join(ROOT, "insts", split_pattern, args.instance))
    if len(paths) == 0:
        print(f"No instances found for {args.instance}, checkout...")
        for split in ['dev', 'test']:
            swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split=split)
            instance = next((item for item in swebench if item['instance_id'] == args.instance), None)
            if not instance is None:
                env = Env(instance, split=split)
                env.reset_work_dir()
                assert os.path.exists(env.work_dir), "Work dir not found"
                paths = [env.work_dir]
                break
        assert len(paths) > 0, f"Instance {args.instance} not found in any split"
    if len(paths) > 1:
        print(f"Multiple instances found for {args.instance}, please specify the split")
        return

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    trace_path = f"{args.instance}.trace.{timestamp}"
    log_path = f"{args.instance}.log.{timestamp}"
    # Set up logging to file
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        handlers=[
                            logging.FileHandler(log_path, 'w', 'utf-8'),
                            logging.StreamHandler()
                        ])

    engine = Engine(trace_path=trace_path)
    engine.register(Shell("shell@localdomain"))
    pm = Agent("user@localdomain", default_model=args.model)
    swe = Agent("swe1@localdomain", default_model=args.model)
    engine.register(pm)
    engine.register(swe)
    engine.load_mbox(args.solver, ENQUEUE_MEMORY)
    engine.run()
    pm.model = args.model
    swe.model = args.model
    os.chdir(os.path.join(paths[0], "testbed"))
    patch_link = os.path.join("..", "patch")
    failed_path = os.path.join("..", "failed")
    if os.path.exists(patch_link):
        if args.force:
            os.remove(patch_link)
        else:
            sys.stderr.write(f"Patch already exists at {patch_link}, not solving\n")
            return
    if os.path.exists(failed_path):
        if args.force:
            os.remove(failed_path)
        else:
            sys.stderr.write(f"Failed already exists at {failed_path}, not solving\n")
            return
    os.system("sudo find . -type d -name '__pycache__' -exec rm -rf {} +")
    os.system("git reset --hard HEAD")

    def stop_condition (cost):
        if os.path.exists(patch_link):
            logging.info(f"A patch was found; solver seems to have succeeded.")
            return True
        if os.path.exists(failed_path):
            logging.info(f"Solver has failed.")
            return True
        if cost > args.budget:
            logging.info(f"Reaching budget {cost:.8f} > {args.budget:.8f}.")
            return True
        return False

    os.system("pwd")
    with aa_context() as aa:
        aa.trials = 0
        aa.max_trials = args.max_trials
    with open("../instance.json", "r") as f:
        meta = json.load(f)
    message = EmailMessage()
    message["From"] = pm.address
    message["To"] = swe.address
    message["Subject"] = "New project"
    message.set_content(f"We are now in a new codebase checked out from https://github.com/{meta['repo']}.  Solve the issue as we did before.  Start by viewing the ticket file ../problem_statement.txt")
    engine.enqueue(message, ENQUEUE_TASK)
    engine.run(stop_condition=stop_condition, debug=args.debug)
    if not os.path.exists(patch_link):
        logging.info(f"No patch was found; solver has failed.")
        if not os.path.exists(failed_path):
            with open(failed_path, "w") as f:
                f.write('test not run')

if __name__ == "__main__":
    pass
