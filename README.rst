carbon
======

Carbon is a tool for generating a feed of people that can be loaded into Symplectic Elements.


Installation
------------

Use pip to install into a virtualenv::

    (carbon)$ pip install https://github.com/MITLibraries/carbon/zipball/master

In order to connect to the data warehouse you will also need to install the `cx_Oracle` python package into your virtualenv. Steps 1-5 detailed at https://blogs.oracle.com/opal/entry/configuring_python_cx_oracle_and should be sufficient.


Usage
-----

View the help menu for the `carbon` command::

    $ carbon --help

Carbon will generate an XML feed that can be uploaded to Symplectic. The command requires an SQLAlchemy database connection string, a feed type and, optionally, an output file. If no output file is specified, the feed will be printed to stdout.::

    (carbon)$ carbon sqlite:///people.db people
