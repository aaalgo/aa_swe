import os
import pickle
from datasets import load_dataset
from aa_swe.swe import ROOT

def main ():
    datasets = {}
    for split in ['dev', 'test']:
        swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split=split)
        dataset = {}
        datasets[split] = dataset
        for instance in swebench:
            instance_id = instance['instance_id']
            dataset[instance_id] = instance
            repo = instance['repo']
            repo_url = f"https://github.com/{instance['repo']}.git"
            repo_dir = os.path.join(ROOT, "repos", instance['repo'])

            if os.path.exists(os.path.join(repo_dir, "config")):
                print(f"repo {repo} already exists, not downloading")
                continue
            os.makedirs(repo_dir, exist_ok=True)
            os.system(f'git clone --no-checkout --bare {repo_url} {repo_dir}')
    with open(os.path.join(ROOT, "datasets.pkl"), "wb") as f:
        pickle.dump(datasets, f)

