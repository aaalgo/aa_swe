The Ann Arbor Software Engineering Agents
=========================================

* Wei Dong / Ann Arbor Algorithms / wdong@aaalgo.com
* Yuanfang Guan / University of Michigan

Solving the [SWE-bench](https://www.swebench.com/) with [Mailcoach](https://github.com/aaalgo/mailcoach_lite).

**You'll need a solver (the agents' memory) to run this package.  The solver is currently
not open to the general public.  Please contact the authors for collaboration.**

# Overview of Data Layout

All data will be contained in a root working directory selected by the user.  The root working directory is specified by the environment variable `AA_SWE_ROOT`.

```
AA_SWE_ROOT
├── repos   (The cloned bare git repos)
│   ├── django/django
│   ├── astropy/astropy
|   ... 
|   
├── insts   (The working directories)
│   ├── test
│   │   ├── sympy__sympy-22005
│   │   │   ├── testbed (The task codebase)
│   │   │   │   ├── instance.json
│   │   │   │   └── stdout....
│   │   │   └── ...
│   │   └── ...
│   └── dev
│       ├── ...
│       └── ...
```

# Setup

## Install Packages

One can install a python package by cloning the git repo, and then running the following command within the top-level directory of the repo:

```
pip3 install -e .
```

Use this method to install the following packages:

- https://github.com/SWE-bench/SWE-bench
- https://github.com/aaalgo/mailcoach_lite
- https://github.com/aaalgo/aa_swe  (This package)

The following commands will be available after installation:

- `swe_download`: download the github repositories for the SWE-bench testbed.
- `swe_solve`: solve an instance.
- `swe_submit`: merge solutions into a jsonl file for evaluation.
- `aa_xxx`: a series of commands for the AI agents.

Note that the `swe_xxx` commands should NOT be made known to the AI agents.  You are allowed to use all the `swe_xxx` and `aa_xxx` commands.

## Building Docker Images

SWE-bench requires building a series of docker images for evaluation.

```
python3 -m swebench.harness.prepare_images --dataset_name princeton-nlp/SWE-bench_Lite --split test --tag REPLACE_ME --max_workers 16
```

You want to replace the tag with your own tag -- something arbitrary that you like.

There are two splits: `test` and `dev`.  Some of the images might fail to build; update your SWE-bench repo in a few days and try again.  They are actively fixing issues.

## Environment Variables

Create a root working directory.  Add the following environment to your `~/.bashrc`:

```
export AA_SWE_ROOT=/path/to/your/root/working/directory
export AA_SWE_DATA_TAG=the_tag_you_used_in_the_docker_build_command
```

## Download the Github Repositories

```
swe_download
```

# Solving Problems

```
swe_solve -i sympy__sympy-22005
```

The following arguments are available:

- `-i,--instance INSTANCE_ID`: the instance id to solve.
- `--split`: the split of the dataset to solve, optional.
- `-b,--budget BUDGET`: the budget limit; will stop when reached.
- `-m,--model MODEL`: the model to use, see `mailcoach__lite/mailcoach_lite/__init__.py`.
- `-d,--debug`: step mode, will ask for confirmation before each step.
- `-f,--force`: for the solve to run over existing data.
- `--max_trials`: maximal number of test failures before giving up.

```
swe_list [--all]
```
This will list the current status of the problems.


```
swe_submit
```

This will merge all solved cases and generate `all_preds_YYYYMMDDHHMMSS.jsonl` for evaluation.
