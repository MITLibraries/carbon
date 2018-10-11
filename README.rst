carbon
======

Carbon is a tool for generating a feed of people that can be loaded into Symplectic Elements. It is designed to be run as a container.

Developing
----------

Use pipenv to install and manage dependencies::

    $ git clone git@github.com:MITLibraries/carbon.git
    $ cd carbon
    $ pipenv install --dev

Connecting to the data warehouse will require installing the ``cx_Oracle`` python package. The good news is that this is now being packaged as a wheel for most architectures, so no extra work is required to install it. If you don't need to actually connect to the data warehouse, you are done. Note that the test suite uses SQLite, so you can develop and test without connecting to the data warehouse.

If you do need to connect to the data warehouse, you will also need to install the Oracle client library. It seems that now just installing the basic light package should be fine. In general, all you should need to do is extract the package and add the extracted directory to your ``LD_LIBRARY_PATH`` environment variable. If there is no ``lbclntsh.so`` (``libclntsh.dylib`` for Mac) symlink in the extracted directory, you will need to create one. The process will look something like this::

    $ unzip instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip -d /usr/local/opt
    # Add the following line to your .bash_profile or whatever to make it permanent
    $ export LD_LIBRARY_PATH=/usr/local/opt/instantclient_18_3:$LD_LIBRARY_PATH
    # If the symlink doesn't already exist:
    $ ln -rs /usr/local/opt/instantclient_18_3/libclntsh.so.18.1 \
        /usr/local/opt/instantclient_18_3/libclntsh.so

On Linux, you will also need to make sure you have libaio installed. You can probably just use your system's package manager to install this easily. The package may be called ``libaio1``.

Building
--------

Running ``make dist`` creates a new container that is tagged as ``carbon:latest``. It will also add tags for the ECR registry with both the ``latest`` and the git short hash. The first build will take some time, but subsequent builds should be fast.

We are restricted from distributing the Oracle client library, so a copy is kept in a private S3 bucket for use when building the container image. If you are updating this, make sure you are using a Linux x86_64 version.

The build process downloads this file from S3 so you should have the AWS CLI installed and configured to authenticate using an account with appropriate access.

Deploying
---------

Deployment is currently being handled by Travis. When a PR is merged onto the master branch Travis will build a new container image, tag it both with ``latest`` and with the git short hash, and then push both tags to the ECR registry.

If you need to deploy a new image outside of Travis then do the following::

    $ cd carbon
    $ make clean
    $ make dist && make publish

Configuration
^^^^^^^^^^^^^

In order for the Lambda to run, carbon needs a few environment variables set. These can either be set in the environment or passed to the Lambda function through the event JSON object. Variables set using the event object will overwrite those set in the environment.

+-----------+-------------------------------------------------------------+
| Variable  | Description                                                 |
+===========+=============================================================+
| FTP_USER  | FTP user to log in as                                       |
+-----------+-------------------------------------------------------------+
| FTP_PASS  | Password for FTP user (see SECRET_ID)                       |
+-----------+-------------------------------------------------------------+
| FTP_PATH  | Name of remote file (with path) on FTP server               |
+-----------+-------------------------------------------------------------+
| FTP_HOST  | FTP server hostname                                         |
+-----------+-------------------------------------------------------------+
| FTP_PORT  | FTP server port                                             |
+-----------+-------------------------------------------------------------+
| CARBON_DB | SQLAlchemy database connection string of the form:          |
|           | ``oracle://<username>:<password>@<server>:1521/<sid>``      |
|           | (see SECRET_ID)                                             |
+-----------+-------------------------------------------------------------+
| SECRET_ID | The ID for an AWS Secrets secret. Use either the Amazon     |
|           | Resource Name or the friendly name of the secret. See below |
|           | for a description of this value.                            |
+-----------+-------------------------------------------------------------+

The ``FTP_PASS`` and ``CARBON_DB`` env vars should not be set as env vars in the Lambda function. Instead, create an AWS Secrets JSON object with these and set the ID of the secret as the ``SECRET_ID`` env var on the Lambda function. The JSON object should look like::

    {
      "FTP_PASS": <password>,
      "CARBON_DB": <connection_string>
    }

The same Lambda function is used to generate both the HR and the AA feeds. Passing the feed type to the Lambda at runtime determines which feed gets generated. This should be handled by the CloudWatch event that triggers the Lambda execution. The event can be configured to pass a custom JSON object to the Lambda. Use the following JSON, selecting either ``people`` or ``articles`` for the feed you want to generate::

    {
      "feed_type": <people|articles>
    }

Usage
-----

While this is intended to be run as a Lambda, the old CLI interface is still supported for ease of testing locally.

View the help menu for the ``carbon`` command::

    $ carbon --help

Carbon will generate an XML feed that can be uploaded to Symplectic. The command requires an SQLAlchemy database connection string, a feed type and, optionally, an output file. For connecting to Oracle use ``oracle://<username>:<password>@<server>:1521/<sid>``. The database connection string can also be passed by an environment variable named ``CARBON_DB``. If no output file is specified, the feed will be printed to stdout.::

    (carbon)$ env CARBON_DB sqlite:///people.db carbon people

