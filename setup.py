#!/usr/bin/env python
"""
setup.py

Coveo S3 Challenge
"""

from setuptools import setup, find_packages

install_requires = [
    'boto3',
    'click'
]


setup(
    name='cs3c',
    version='1.0.0',
    install_requires=install_requires,
    description='S3 bucket information CLI. Not a catchy name, but it works.',
    author='Jacob Cook',
    author_email='jacob@peakwinter.net',
    packages=find_packages(),
    test_suite='tests',
    entry_points={
        'console_scripts': ['cs3c = cs3c:cli'],
    }
)
