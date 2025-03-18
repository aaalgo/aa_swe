from setuptools import setup, find_packages

setup(
    name='aa_swe',
    version='0.1',
    packages=find_packages(),
    scripts=['aa_swe/aa_open.py'],
    package_data={
        'aa_swe': ['data/survey.csv'], 
    },    
    entry_points={
        'console_scripts': [
            'aa_init=aa_swe.aa_init:main',
            'aa_open=aa_swe.aa_open:main',
            'aa_close=aa_swe.aa_close:main',
            'aa_search=aa_swe.aa_search:main',
            'aa_list=aa_swe.aa_list:main',
            'aa_scroll=aa_swe.aa_scroll:main',
            'aa_create=aa_swe.aa_create:main',
            'aa_select=aa_swe.aa_select:main',
            'aa_rewrite=aa_swe.aa_rewrite:main',
            'aa_ticket=aa_swe.aa_ticket:main',
            'aa_find_def=aa_swe.aa_find_def:main',
            'aa_find_class=aa_swe.aa_find_class:main',
            'aa_test=aa_swe.aa_test:main',
            'swe_shell=aa_swe.swe_solve:shell_main',

            'swe_checkout=aa_swe.swe_checkout:main',
            'swe_download=aa_swe.swe_download:main',
            'swe_submit=aa_swe.swe_submit:main',
            'swe_list=aa_swe.swe_list:main',
            'swe_reveal=aa_swe.swe_reveal:main',
            'swe_cheat=aa_swe.aa_swe:cheat_main',
            #'swe_run=aa_swe.aa_swe_docker:run_main',
            'swe_solve=aa_swe.swe_solve:main',
            'swe_dump=aa_swe.swe_dump:main',
            'swe_analyze=aa_swe.swe_analyze:main',
            'swe_eval=aa_swe.swe_eval:main',
            'swe_mbox=aa_swe.swe_mbox:main',
            'swe_stat=aa_swe.swe_stat:main',
            'swe_poll=aa_swe.swe_poll:main',
            'swe_poll2=aa_swe.swe_poll2:main',
            'swe_build_docker=aa_swe.swe_build_docker:main',
        ],
    },
    include_package_data=True,
    install_requires=[
    ],
)
