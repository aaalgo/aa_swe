import json

def main ():
    with open('../instance.json', 'r') as f:
        instance = json.load(f)
    print(instance['patch'])