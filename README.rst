carbon
======

Carbon is a tool for generating a feed of people that can be loaded into Symplectic Elements.


Installation
------------

In order to connect to the data warehouse you will need to install the ``cx_Oracle`` python package into your virtualenv. Steps 1-5 detailed at https://blogs.oracle.com/opal/entry/configuring_python_cx_oracle_and should be sufficient.

Once the Oracle package has been installed clone the repo::

    (carbon)$ git clone https://github.com/MITLibraries/carbon.git

Then use pip to install::

    (carbon)$ cd carbon && pip install .


Updating
--------

To update carbon, update the local repo and then upgrade the local package::

    (carbon)$ cd carbon && git pull
    (carbon)$ pip install -U .


Usage
-----

View the help menu for the ``carbon`` command::

    $ carbon --help

Carbon will generate an XML feed that can be uploaded to Symplectic. The command requires an SQLAlchemy database connection string, a feed type and, optionally, an output file. For connecting to Oracle use ``oracle://<username>:<password>@<server>:1521/<sid>``. The database connection string can also be passed by an environment variable named ``CARBON_DB``. If no output file is specified, the feed will be printed to stdout.::

    (carbon)$ env CARBON_DB sqlite:///people.db carbon people

