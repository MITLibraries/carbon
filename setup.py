# -*- coding: utf-8 -*-
"""
Carbon, a people loader.
"""

import io
import re
from setuptools import find_packages, setup


with io.open('LICENSE') as f:
    license = f.read()

with open('carbon/__init__.py', 'r') as fp:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fp.read(),
                        re.MULTILINE).group(1)

setup(
    name='carbon',
    version=version,
    description='Load people into Elements',
    long_description=__doc__,
    url='https://github.com/MITLibraries/carbon',
    license=license,
    author='Mike Graves',
    author_email='mgraves@mit.edu',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'click',
        'lxml',
        'SQLAlchemy',
    ],
    entry_points={
        'console_scripts': [
            'carbon = carbon.cli:main',
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ]
)