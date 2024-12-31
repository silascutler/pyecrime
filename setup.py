# setup.py

from setuptools import setup, find_packages

setup(
    name="ecrime",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'Click',
        'requests',
        'textwrap',
    ],
    entry_points={
        'console_scripts': [
            'ecrime=ecrime:cli',
        ],
    },
    author="Silas Cutler",
    author_email="silas@p1nk.io",
    description="A CLI tool for ecrime.ch",
    url="https://github.com/silascutler/ecrimech_client",
)