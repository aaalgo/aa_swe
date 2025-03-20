import os

def main ():
    AA_SWE_WORK_DIR = os.path.abspath(os.getcwd())
    os.environ['AA_SWE_WORK_DIR'] = AA_SWE_WORK_DIR
    os.environ['PS1'] = 'aa_swe> '
    os.system('bash --norc')