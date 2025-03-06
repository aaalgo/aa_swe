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
            'aa_open=aa_swe.aa_open:main',
            'aa_close=aa_swe.aa_close:main',
            'aa_search=aa_swe.aa_search:main',
            'aa_list=aa_swe.aa_list:main',
            'aa_scroll=aa_swe.aa_scroll:main',
            'aa_create=aa_swe.aa_create:main',
            'aa_edit=aa_swe.aa_edit:main',
            'aa_select=aa_swe.aa_edit:select_main',
            'aa_rewrite=aa_swe.aa_edit:rewrite_main',
            'aa_ticket=aa_swe.aa_ticket:main',
            'aa_tree=aa_swe.aa_tree:main',
            'aa_test=aa_swe.aa_swe_docker:test_main',
            'swe_checkout=aa_swe.aa_swe:checkout_main',
            'swe_list=aa_swe.aa_swe:list_main',
            'swe_reveal=aa_swe.swe_reveal:main',
            'swe_run=aa_swe.aa_swe_docker:run_main',
            'swe_solve=aa_swe.aa_swe:solve_main',
            'swe_dump=aa_swe.swe_dump:main',
            'swe_download=aa_swe.aa_swe:download_main',
            'swe_submit=aa_swe.swe_submit:main',
            'swe_analyze=aa_swe.swe_analyze:main',
            'swe_eval=aa_swe.swe_eval:main',
            'swe_cheat=aa_swe.aa_swe:cheat_main',
            'swe_mbox=aa_swe.swe_mbox:main',
            'swe_stat=aa_swe.swe_stat:main',
        ],
    },
    include_package_data=True,
    install_requires=[
        'datasets',  # Add your dependencies here
    ],
)
