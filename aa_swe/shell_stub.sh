#!/bin/bash
source /opt/miniconda3/bin/activate
conda activate testbed
cd /aa_swe
/usr/bin/python3 -m pip install .
aa_init
cd /testbed
export AA_SWE_WORK_DIR=/output
/usr/bin/python3 /shell_stub.py
