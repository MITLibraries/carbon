# -*- coding: utf-8 -*-
"""
Carbon, a people loader.
"""

from setuptools import find_packages, setup
import subprocess

with open("LICENSE") as f:
    license = f.read()

try:
    output = subprocess.run(
        ["git", "describe", "--always"], stdout=subprocess.PIPE, encoding="utf-8"
    )
    version = output.stdout.strip()
except subprocess.CalledProcessError:
    version = "unknown"

setup(
    name="carbon",
    version="1.0.0-" + version,
    description="Load people into Elements",
    long_description=__doc__,
    url="https://github.com/MITLibraries/carbon",
    license=license,
    author="Mike Graves",
    author_email="mgraves@mit.edu",
    packages=find_packages(exclude=["tests"]),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "carbon = carbon.cli:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
)
