import sys
import os
import time
import datetime
import subprocess as sp
import json
import mailcoach
import logging
import argparse
from mailcoach import Engine, Agent, EmailMessage, ENQUEUE_MEMORY, ENQUEUE_TASK, DEFAULT_MODEL, ACTION_TO
from mailcoach.robots import Shell
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
from aa_swe.swe import ROOT, load_instance
STUB_PORT = 8642


class DockerShell (Shell):
    # This class creates and maintains a working directory for the
    # instance and runs the docker shell on it.

    def __init__ (self, address, instance_id, output_dir, timestamp, max_trials=5):
        # address: robot address
        # instance_id: instance ID
        self.docker_image = f"aa_swe.{instance_id}"
        self.container_name = f"{instance_id}-{timestamp}"
        self.max_trials = max_trials
        self.trials = 0
        self.output_dir = os.path.abspath(output_dir)

        result = sp.run(f"docker image inspect {self.docker_image}:latest >/dev/null 2>&1", shell=True)
        if result.returncode != 0:
            print(f"Docker image {self.docker_image}:latest does not exist. Rebuilding")
            os.system(f"swe_build_docker -i {instance_id}")

        instance = load_instance(instance_id)
        self.instance = instance
        with open(os.path.join(self.output_dir, "instance.json"), "w") as f:
            json.dump(instance, f)
        stub_path = os.path.join(os.path.dirname(mailcoach.__file__), "shell_stub.py")
        stub_path = os.path.abspath(stub_path)
        assert os.path.exists(stub_path), f"shell_stub.py not found at {stub_path}"
        aa_swe_path = os.path.dirname(os.path.dirname(__file__))
        aa_swe_path = os.path.abspath(aa_swe_path)

        command = ["docker", "run", "--rm",
                    "-v", f"{stub_path}:/shell_stub.py",
                    "-v", f"{aa_swe_path}:/aa_swe",
                    "-v", f"{self.output_dir}:/output",
                    "--name", self.container_name,
                    self.docker_image,
                    "/aa_swe/aa_swe/shell_stub.sh"
                    ]
        self.handle = sp.Popen(command)
        self.container_ip = None
        for i in range(150):
            try:
                if self.container_ip is None:
                    self.container_ip = sp.check_output("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + self.container_name + " 2>/dev/null", shell=True).decode('ascii').strip()
                    super().__init__(address, f"http://{self.container_ip}:{STUB_PORT}")
                print("Container IP is", self.container_ip)
                out = self.run_remote_command("true", None)
                break
            except:
                pass
            print(f"Waiting for container ({self.container_ip}) to start...")
            time.sleep(2)
        assert self.container_ip is not None, f"Failed to start container {self.docker_image} as {self.container_name}"
        print(f"Docker stub has started at http://{self.container_ip}:{STUB_PORT}")

    def shutdown (self):
        os.system(f"docker kill {self.container_name}")
        self.handle.wait()
        self.handle = None

    def handle_test_output (self, output):
        stdout_path = os.path.join(self.output_dir, f"stdout.{self.trials}")
        self.trials += 1
        with open(stdout_path, "w") as f:
            f.write(output)
        output = sp.check_output(f"swe_eval {stdout_path} 2> /dev/null", shell=True).decode('utf-8')
        success = 'Congratulations!' in output
        if success:
            self.run_remote_command('cd /testbed && git diff > /output/patch', None)
            assert os.path.exists(os.path.join(self.output_dir, "patch")), f"Patch file not found at {os.path.join(self.output_dir, 'patch')}"
        else:
            if self.trials >= self.max_trials:
                os.system(f"touch {self.output_dir}/failed")
        return output

    def run_remote_command (self, command, timeout=None):
        resp = super().run_remote_command(command, timeout)
        if command.strip() == 'aa_test':
            resp.stdout = self.handle_test_output(resp.stdout)
        return resp

def shell_main ():
    import argparse
    parser = argparse.ArgumentParser(description='Test docker shell')
    parser.add_argument('-i', '--instance', type=str, required=True, help='The instance ID to process')
    args = parser.parse_args()
    assert not args.instance is None

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = f"{args.instance}.{timestamp}"
    os.makedirs(output_dir, exist_ok=False)
    shell = DockerShell("swe1@localdomain", args.instance, output_dir, timestamp)

    while True:
        try:
            line = input()
            if not line:
                continue
            if line == 'exit':
                shell.shutdown()
                break
            out = shell.run_remote_command(line, None)
            print(out.returncode)
            print('-'* 20, 'stdout', '-'* 20)
            print(out.stdout)
            print('-'* 20, 'stderr', '-'* 20)
            print(out.stderr)
        except EOFError:
            break

def main ():
    if os.path.exists("quit"):
        print("Found quit file, not solving")
        return
    from glob import glob
    parser = argparse.ArgumentParser(description='Process an mbox file.')
    parser.add_argument('-s', '--solver', default='solver.mbox', help='Path to solver memory.')
    parser.add_argument('-i', '--instance', type=str, required=True, help='The instance ID to process')
    parser.add_argument('-b', '--budget', type=float, default=0.05, help='The budget')
    parser.add_argument('-m', '--model', default='openai/gpt-4o-mini', help='The model to use.')
    parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
    parser.add_argument('-f', '--force', action='store_true', help='Force the operation to run even if conditions are not met')
    parser.add_argument('--max_trials', type=int, default=8, help='The maximum number of trials allowed')
    parser.add_argument('--team', action='store_true', help='Team mode')
    args = parser.parse_args()
    if not os.path.exists(args.solver):
        print(f"Solver {args.solver} not found.")
        return
    patches = list(glob(os.path.join(args.instance + '.*', "patch")))
    failures = list(glob(os.path.join(args.instance + '.*', "failed")))
    if len(patches) + len(failures) > 0:
        if not args.force:
            sys.stderr.write(f"Work directories already exist, not solving\n")
            return

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = f"{args.instance}.{timestamp}"
    os.makedirs(output_dir, exist_ok=False)
    trace_path = f"{output_dir}/trace.mbox"
    log_path = f"{output_dir}/log.txt"
    patch_path = f"{output_dir}/patch"
    failed_path = f"{output_dir}/failed"
    # Set up logging to file
    logging.root.handlers = []
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        handlers=[
                            logging.FileHandler(log_path),
                            logging.StreamHandler(sys.stdout)
                        ])
    logging.info("Logging setup complete. Log file path: %s", log_path)

    engine = Engine(trace_path=trace_path, allow_new_agents=True)
    shell = DockerShell("shell@localdomain", args.instance, output_dir, timestamp)
    engine.register(shell)
    pm = Agent("user@localdomain", default_model=args.model)
    swe = Agent("swe@localdomain", default_model=args.model)
    engine.register(pm)
    engine.register(swe)
    engine.load_mbox(args.solver, ENQUEUE_MEMORY)
    engine.run()
    pm.model = args.model
    swe.model = args.model

    def stop_condition (cost):
        if os.path.exists(patch_path):
            logging.info(f"A patch was found; solver seems to have succeeded.")
            return True
        if os.path.exists(failed_path):
            logging.info(f"Solver has failed.")
            return True
        if cost > args.budget:
            logging.info(f"Reaching budget {cost:.8f} > {args.budget:.8f}.")
            return True
        return False

    message = EmailMessage()
    if args.team:
        adviser = engine.entities.get("adviser@localdomain", None)
        inv_swe = engine.entities.get("inv.swe@localdomain", None)
        test_swe = engine.entities.get("test.swe@localdomain", None)
        assert not inv_swe is None and not test_swe is None and not adviser is None
        adviser.model = 'openai/gpt-4o'
        inv_swe.model = args.model
        test_swe.model = args.model
        # but do not register them; or they won't be cloned
        message1 = EmailMessage()
        message1["From"] = pm.address
        message1["To"] = swe.address
        message1["X-Expect"] = f"{test_swe.address}, {inv_swe.address}"
        message1["X-Drop"] = "true"
        message1.set_content("")
        engine.enqueue(message1, ENQUEUE_TASK)

        message["To"] = f"{test_swe.address}, {inv_swe.address}, {swe.address}"
        message["Cc"] = f"{adviser.address}"
    else:
        message["To"] = swe.address
    message["From"] = pm.address
    message["Subject"] = f"New ticket: {args.instance}"
    message["X-Hint-Model"] = args.model
    content = "We are now in a new codebase.  Below is the description of the ticket we need to solve.\n--- ticket ---\n"
    content += shell.instance['problem_statement']
    message.set_content(content)
    engine.enqueue(message, ENQUEUE_TASK)
    engine.run(stop_condition=stop_condition, debug=args.debug)
    if not os.path.exists(patch_path):
        logging.info(f"No patch was found; solver has failed.")
        if not os.path.exists(failed_path):
            with open(failed_path, "w") as f:
                f.write('test not run')