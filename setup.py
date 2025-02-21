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
            'aa_view=aa_tools.aa_view:main',
            'aa_scroll=aa_tools.aa_scroll:main',
            'aa_create=aa_tools.aa_create:main',
        ],
    },
    include_package_data=True,
)
