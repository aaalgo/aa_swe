from setuptools import setup, find_packages

setup(
    name='aa_tools',
    version='0.1',
    packages=find_packages(),
    scripts=['aa_tools/aa_open.py'],
    entry_points={
        'console_scripts': [
            'aa_open=aa_tools.aa_open:main',
            'aa_close=aa_tools.aa_close:main',
            'aa_search=aa_tools.aa_search:main',
            'aa_list=aa_tools.aa_list:main',
            'aa_scroll=aa_tools.aa_scroll:main',
            'aa_create=aa_tools.aa_create:main',
            'aa_edit=aa_tools.aa_edit:main',
            'aa_ticket=aa_tools.aa_ticket:main',
            'aa_tree=aa_tools.aa_tree:main',
            'aa_test=aa_tools.aa_swe_docker:test_main',
            'swe_checkout=aa_tools.aa_swe:checkout_main',
            'swe_list=aa_tools.aa_swe:list_main',
            'swe_reveal=aa_tools.swe_reveal:main',
            'swe_run=aa_tools.aa_swe_docker:run_main',
            'swe_solve=aa_tools.aa_swe:solve_main',
        ],
    },
    include_package_data=True,
)
