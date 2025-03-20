#!/usr/bin/env python3
import os
import subprocess as sp

def main ():
    if os.path.exists("./_aa_test"):
        os.system("./_aa_test")
        return
    os.chdir('/testbed')
    sp.run("/meta/patched_eval.sh 2>&1", shell=True)

