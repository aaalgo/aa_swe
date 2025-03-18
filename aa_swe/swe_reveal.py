import sys
import json

def main ():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            for l in f:
                if instance['instance_id'] in l:
                    s = json.loads(l)
                    print(s['model_patch'])
                    break
        return
    instance = None
    for path in ['../instance.json', './instance.json']:
        try:
            with open(path, 'r') as f:
                instance = json.load(f)
        except:
            continue
    if instance is None:
        return
    if len(sys.argv) == 1:
        print(instance['patch'])
        return