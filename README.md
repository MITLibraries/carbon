# Carbon

Carbon is a tool for generating a feed of people that can be loaded into Symplectic Elements. It is designed to be run as a container. This document contains general application information. Please refer to the [mitlib-tf-workloads-carbon](https://github.com/mitlibraries/mitlib-tf-workloads-carbon) for the deployment configuration.

## Development

* To install with dev dependencies: `make install`
* To update dependencies: `make update`
* To run unit tests: `make test`
* To lint the repo: `make lint`
* To run the app: `pipenv run carbon --help`

The Data Warehouse runs on a older version of Oracle that necessitates the thick mode of python-oracledb which requires the Oracle Instant Client Library (this app was developed with version 21.9.0.0.0.). The test suite uses SQLite, so you can develop and test without connecting to the Data Warehouse.

If you do need to connect to the data warehouse, you have two options, one using Docker and one without.

### With Docker

Note: as of this writing, the Apple M1 Macs cannot run Oracle Instant Client, so Docker is the only option for development on those machines.

From the project folder:

1. Run `make dependencies` with appropriate AWS credentials.

2. Run `make dist-dev`` to build the container.

3. Run `docker run carbon-dev:latest`.

### Without Docker

1. Download Oracle Instant Client (basiclite is sufficient) and set the ORACLE_LIB_DIR env variable.

2. Run pipenv run patronload.

## Deploying

In the AWS Organization, we have a automated pipeline from Dev --> Stage --> Prod, handled by GitHub Actions.

### Staging

When a PR is merged onto the `main` branch, Github Actions will build a new container image, tag it both with `latest`, the git short hash, and the PR number, and then push the container with all the tags to the ECR repository in Stage. An EventBridge scheduled event will periodically trigger the Fargate task to run. This task will use the latest image from the ECR registry.

### Production

Tagging a release on the `main` branch will promote a copy of the `latest` container from Stage-Worklods to Prod.

## Configuration

The Fargate task needs the following arguments passed in at runtime.

| Argument | Description |
|----------|-------------|
| --ftp | |
| --sns-topic | The ARN for the SNS topic. This is used to send an email notification. |
| \<feed_type\> | The type of feed to run. This should be either `people` or `articles`. |

The ECS Fargate task also makes use of the following environment variables.

| Argument | Description |
|----------|-------------|
| `CARBON_DB` | an SQLAlchemy database connection string of the form `oracle://<username>:<password>@<server>:1521/<sid>`. |
| `FTP_HOST` | Hostname of FTP server |
| `FTP_PORT` | FTP server port |
| `FTP_USER` | FTP username |
| `FTP_PASS` | FTP password |
| `FTP_PATH` | Full path to file on FTP server |

These values are all set in the ECS Task Definition by the Terraform code in [mitlib-tf-workloads-carbon](https://github.com/mitlibraries/mitlib-tf-workloads-carbon).

## Usage

The CLI interface works the same whether running locally or as a container. When running as a container, however, remember that if specifying an output file (rather than stdout) it will go to a file local to the container, not your host system.

View the help menu for the `carbon` command::

```bash
carbon --help
```

Carbon will generate an XML feed that can be uploaded to Symplectic. The command requires an SQLAlchemy database connection string, a feed type and, optionally, an output file. For connecting to Oracle use `oracle://<username>:<password>@<server>:1521/<sid>`. The database connection string can also be passed by an environment variable named `CARBON_DB`. If no output file is specified, the feed will be printed to stdout.

```bash
(carbon)$ env CARBON_DB sqlite:///people.db carbon people
```
