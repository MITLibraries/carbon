======
Carbon
======

Carbon is a tool for generating a feed of people that can be loaded into Symplectic Elements. It is designed to be run as a container. This document contains general application information. Please refer to the `Terraform module <https://github.com/MITLibraries/mitlib-terraform/tree/master/apps/carbon>`_ for the deployment configuration.

.. contents:: Table of Contents
.. section-numbering::

Developing
----------

Use pipenv to install and manage dependencies::

    $ git clone git@github.com:MITLibraries/carbon.git
    $ cd carbon
    $ pipenv install --dev

Connecting to the data warehouse will require installing the ``cx_Oracle`` python package. The good news is that this is now being packaged as a wheel for most architectures, so no extra work is required to install it. If you don't need to actually connect to the data warehouse, you are done. Note that the test suite uses SQLite, so you can develop and test without connecting to the data warehouse.

If you do need to connect to the data warehouse, you have two options, one using Docker and one without.

Without Docker
^^^^^^^^^^^^^^

To connect without Docker you will need to install the `Oracle client library <https://www.oracle.com/technetwork/database/database-technologies/instant-client/overview/index.html>`_. It seems that now just installing the basic light package should be fine. In general, all you should need to do is extract the package and add the extracted directory to your ``LD_LIBRARY_PATH`` environment variable. If there is no ``lbclntsh.so`` (``libclntsh.dylib`` for Mac) symlink in the extracted directory, you will need to create one. The process will look something like this (changing for paths/filenames as necessary)::

    $ unzip instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip -d /usr/local/opt

    # Add the following line to your .bash_profile or whatever to make it permanent
    $ export LD_LIBRARY_PATH=/usr/local/opt/instantclient_18_3:$LD_LIBRARY_PATH

    # If the symlink doesn't already exist:
    $ ln -rs /usr/local/opt/instantclient_18_3/libclntsh.so.18.1 \
        /usr/local/opt/instantclient_18_3/libclntsh.so

On Linux, you will also need to make sure you have libaio installed. You can probably just use your system's package manager to install this easily. The package may be called ``libaio1``.

With Docker
^^^^^^^^^^^

Connecting with Docker, in theory, should be more straightforward. The idea would be to test your changes in a container. As long as you aren't modifying the project dependencies, building the container should be quick, so iterating shouldn't be terrible. You will of course need a working Docker installation, and you will also need to have the AWS CLI installed and configured. Your development process using this method would look like:

1. Make your changes.
2. Run ``make dist`` from project root.
3. Test your changes by running ``docker run --rm carbon <carbon args>``, with ``<carbon args>`` being whatever arguments you would normally use to run carbon.

Building
--------

Running ``make dist`` creates a new container that is tagged as ``carbon:latest``. It will also add tags for the ECR registry with both the ``latest`` and the git short hash. The first build will take some time, but subsequent builds should be fast.

We are restricted from distributing the Oracle client library, so a copy is kept in a private S3 bucket for use when building the container image. If you are updating this, make sure you are using a Linux x86_64 version.

The build process downloads this file from S3 so you should have the AWS CLI installed and configured to authenticate using an account with appropriate access.

Deploying
---------

Staging
^^^^^^^

Lacking a fully automated deployment pipeline, the final step of deploying to prod will need to be done manually. Staging builds are fully automated by Github Actions. When a PR is merged onto the main branch Github Actions will build a new container image, tag it both with ``latest`` and with the git short hash, and then push both tags to the ECR staging registry. A Cloudwatch scheduled event will periodically trigger the Fargate task to run. This task will use the latest image from the ECR registry.

If you need to deploy a new image outside of Github Actions then do the following::

    $ cd carbon
    $ make clean
    $ make dist && make publish

Production
^^^^^^^^^^

When you are ready to deploy the current staging build to production, simply run::

  $ make promote

from the project root. This command effectively copies the latest staging image over to the latest production image. In addition, a new tag with the current ISO 8601 formatted UTC datetime is added to the current production image and pushed as well. This is done to make rolling back changes easier. In case this is needed, find the datetime tag of the last working production image and retag it as ``latest``. This can be done with the following, replacing ``<datetime>`` with the datetime tag::

	$ $(aws ecr get-login --no-include-email --region us-east-1)
	$ docker pull 672626379771.dkr.ecr.us-east-1.amazonaws.com/carbon-prod:<datetime>
	$ docker tag 672626379771.dkr.ecr.us-east-1.amazonaws.com/carbon-prod:<datetime> \
      672626379771.dkr.ecr.us-east-1.amazonaws.com/carbon-prod:latest
	docker push 672626379771.dkr.ecr.us-east-1.amazonaws.com/carbon-prod:latest

Configuration
^^^^^^^^^^^^^

The Fargate task needs the following arguments passed in at runtime. These are set in the Terraform config.

+-------------+-------------------------------------------------------------+
| Argument    | Description                                                 |
+=============+=============================================================+
| --ftp       |                                                             |
+-------------+-------------------------------------------------------------+
| --ftp-host  | FTP server hostname                                         |
+-------------+-------------------------------------------------------------+
| --ftp-user  | FTP user to log in as                                       |
+-------------+-------------------------------------------------------------+
| --ftp-path  | Name of remote file (with path) on FTP server               |
+-------------+-------------------------------------------------------------+
| --secret-id | The ID for an AWS Secrets secret. Use either the Amazon     |
|             | Resource Name or the friendly name of the secret. See below |
|             | for a description of this value.                            |
|             |                                                             |
+-------------+-------------------------------------------------------------+
| --sns-topic | The ARN for the SNS topic. This is used to send an email    |
|             | notification.                                               |
+-------------+-------------------------------------------------------------+
| <feed type> | The type of feed to run. This should be either ``people``   |
|             | or ``articles``.                                            |
+-------------+-------------------------------------------------------------+

The ``--secret-id`` option should point to an AWS Secrets JSON object that looks like::

    {
      "FTP_PASS": <password>,
      "CARBON_DB": <connection_string>
    }

``CARBON_DB`` should be an SQLAlchemy database connection string of the form ``oracle://<username>:<password>@<server>:1521/<sid>``.

Usage
-----

The CLI interface works the same whether running locally or as a container. When running as a container, however, remember that if specifying an output file (rather than stdout) it will go to a file local to the container, not your host system.

View the help menu for the ``carbon`` command::

    $ carbon --help

Carbon will generate an XML feed that can be uploaded to Symplectic. The command requires an SQLAlchemy database connection string, a feed type and, optionally, an output file. For connecting to Oracle use ``oracle://<username>:<password>@<server>:1521/<sid>``. The database connection string can also be passed by an environment variable named ``CARBON_DB``. If no output file is specified, the feed will be printed to stdout.::

    (carbon)$ env CARBON_DB sqlite:///people.db carbon people
