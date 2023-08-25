# Carbon

Carbon is a tool for generating a feed of people that can be loaded into Symplectic Elements. It is designed to be run as a container. This document contains general application information. Please refer to the [mitlib-tf-workloads-carbon](https://github.com/mitlibraries/mitlib-tf-workloads-carbon) for the deployment configuration.

## Development

* To install with dev dependencies: `make install`
* To update dependencies: `make update`
* To run unit tests: `make test`
* To lint the repo: `make lint`
* To run the app: `pipenv run carbon --help`

The Data Warehouse runs on an older version of Oracle that necessitates the `thick` mode of python-oracledb, which requires the Oracle Instant Client Library (this app was developed with version 21.9.0.0.0). The test suite uses SQLite, so you can develop and test without connecting to the Data Warehouse.

**Note:** One of the unit tests (`test_cli_connection_tests_fail`) checks that an error message is returned if the app fails to connect to the Data Warehouse. With the current structure of the application, which relies on a single SQLAlchemy engine that is created in `db.py`, this test must be run at the end because it modifies the content of the engine that would cause other tests to fail. This "bug" (not technically a breaking change) will be addressed in later efforts to enhance the Carbon application.

### With Docker

**Note:** As of this writing, the Apple M1 Macs cannot run Oracle Instant Client, so Docker is the only option for development on those machines.

From the project folder:

1. Export AWS credentials for the `dev1` environment.

2. Run `make dependencies` to download the Oracle Instant Client from S3.

3. Run `make dist-dev` to build the Docker container image.

4. Run `make publish-dev` to push the Docker container image to ECR for the `dev1` environment. 

5. Run any `make` commands for testing the application.

Any tests that involve connecting to the Data Warehouse will need to be run as an ECS task in the `stage` environment, which requires building and publishing the Docker container image to ECR for `stage`. As noted in step 1, the appropriate AWS credentials for `stage` must be set to run the commands for building and publishing the Docker container image. The `ECR_NAME_STAGE` and `ECR_URL_STAGE` environment variables must also be set; the values correspond to the 'Repository name' and 'URI' indicated on ECR for the container image, respectively.


### Without Docker

1. Download Oracle Instant Client (basiclite is sufficient) and set the `ORACLE_LIB_DIR` env variable.

2. Run `pipenv run carbon`.

## Connecting to the Data Warehouse

The password for the Data Warehouse is updated each year. To verify that the updated password works, the app must be run as an ECS task in `stage` because Cloudconnector is not enabled in `dev1`. The app can run a database connection test when called with the flag, `--run_connection_tests`.

1. Export stage credentials and set `ECR_NAME_STAGE` and `ECR_URL_STAGE` env variables.
2. Run `make install`.
3. Run `make run-connection-tests-stage`.
4. View the logs from the ECS task run on CloudWatch.
   * On CloudWatch, select the `carbon-ecs-stage` log group.
   * Select the most recent log stream.
   * Verify that the following log is included:
      > Successfully connected to the Data Warehouse: \<VERSION NUMBER\>

## Deploying

In the AWS Organization, we have a automated pipeline from Dev --> Stage --> Prod, handled by GitHub Actions.

### Staging

When a PR is merged onto the `main` branch, Github Actions will build a new container image, tag it both with `latest`, the git short hash, and the PR number, and then push the container with all the tags to the ECR repository in Stage. An EventBridge scheduled event will periodically trigger the Fargate task to run. This task will use the latest image from the ECR registry.

### Production

Tagging a release on the `main` branch will promote a copy of the `latest` container from Stage-Worklods to Prod.

## Usage

The Carbon application retrieves 'people' records from the Data Warehouse and generates an XML file that is uploaded to the Symplectic Elements FTP server. On Symplectic Elements, a job is scheduled to ingest the data from the XML file to create user accounts.

**Note:** The Carbon application can also retrieve 'articles' records, but as of this writing, it is not known whether this feature is still actively used.

## Required ENV

* `FEED_TYPE` = The type of feed and is set to either "people" or "articles".
* `CONNECTION_STRING` = The connection string of the form `oracle://<username>:<password>@<server>:1521/<sid>` for the Data Warehouse.
* `SNS_TOPIC` = The ARN for the SNS topic used for sending email notifications.
* `SYMPLECTIC_FTP_HOST` = The hostname of the Symplectic FTP server.
* `SYMPLECTIC_FTP_PORT` = The port of the Symplectic FTP server.
* `SYMPLECTIC_FTP_USER` = The username for accessing the Symplectic FTP server.
* `SYMPLECTIC_FTP_PASS` = The password for accessing the Symplectic FTP server.
* `SYMPLECTIC_FTP_PATH` = The full file path to the XML file (including the file name) that is uploaded to the Symplectic FTP server.
* `WORKSPACE` = Set to `dev` for local development. This will be set to `stage` and `prod` in those environments by Terraform.



## Optional ENV

* `LOG_LEVEL` = The log level for the `carbon` application. Defaults to `INFO` if not set.
* `ORACLE_LIB_DIR` = The directory containing the Oracle Instant Client library.
* `SENTRY_DSN` = If set to a valid Sentry DSN, enables Sentry exception monitoring. This is not needed for local development.