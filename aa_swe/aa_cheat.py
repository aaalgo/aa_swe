import os

def main ():
    cwd = os.getcwd()
    if os.path.basename(cwd) == "testbed":
        os.chdir("..")
    assert os.path.exists("testbed")
    assert os.path.exists("groundtruth")
    os.system(f"cd testbed && git reset --hard HEAD && git apply ../groundtruth")

