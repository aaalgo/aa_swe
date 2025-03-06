#!/usr/bin/env python3
from glob import glob
import mailbox
import numpy as np
import pandas as pd

def get_latest_trace_files():
    trace_files = glob('*.trace.*')
    latest_files = {}

    for file in trace_files:
        instance_id, _, timestamp = file.split('.')
        if instance_id not in latest_files or timestamp > latest_files[instance_id][0]:
            latest_files[instance_id] = (timestamp, file)
    return [(instance_id, file_info[1]) for instance_id, file_info in latest_files.items()]

def extract_info (path):
    mbox = mailbox.mbox(path)
    begun = False
    inputs = []
    outputs = []
    for msg in mbox:
        #msg = message.get_payload()
        if 'Subject' in msg:
            subject = msg['Subject']
            if isinstance(subject, str) and subject.startswith('New ticket'):
                begun = True
        if not begun:
            continue
        input = msg.get('M-Tokens-Input', '')
        output = msg.get('M-Tokens-Output', '')
        if input:
            inputs.append(int(input))
        if output:
            outputs.append(int(output))
    if len(inputs) != len(outputs):
        assert False
    if len(inputs) == 0:
        return None
    return {
        'max_input': inputs[-1],
        'average_output': np.mean(outputs),
        'steps': len(inputs)
    }


def main ():
    df = []
    for instance_id, file in get_latest_trace_files():
        print(f"{instance_id}: {file}")
        e = extract_info(file)
        if e:
            df.append(e)
    df = pd.DataFrame(df)
    print(df.describe())


if __name__ == "__main__":
    main()