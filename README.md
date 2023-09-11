# Carbon

Carbon is a tool for loading data into [Symplectic Elements](https://support.symplectic.co.uk/support/solutions/articles/6000049890-symplectic-elements-quick-start-guide). Carbon retrieves records from the Data Warehouse, normalizes and writes the data to XML files, and uploads the XML files to the Elements FTP server. It is used to create and run the following feed types: 

   * `people`: Provides data for the HR Feed.
   * `articles`: Provides data for the Publications Feed.

Please refer to the [mitlib-tf-workloads-carbon](https://github.com/mitlibraries/mitlib-tf-workloads-carbon) for the deployment configuration.

## Development

* To install with dev dependencies: `make install`
* To update dependencies: `make update`
* To lint the repo: `make lint`

The Data Warehouse runs on an older version of Oracle that necessitates the `thick` mode of `python-oracledb`, which requires the Oracle Instant Client Library (this app was developed with version 21.9.0.0.0).

### Running the test suite

The test suite uses SQLite, so you can develop and test without connecting to the Data Warehouse.

1. Run `make test` to run unit tests.

### Running the application on your local machine

1. Export AWS credentials for the `Dev1` environment.
2. Create a `.env` file at the root folder of the Carbon repo, and set the required environment variables described in [Required Env](#required-env).

   **Note**: The host for the Data Warehouse is different when connecting from outside of AWS (which uses Cloudconnector). For assistance, reach out to the [Data Warehouse team](https://ist.mit.edu/warehouse).

3. If the run requires a connection to the Data Warehouse, connect to an approved VPN client. Otherwise, skip this step.
4. Follow the steps relevant to the machine you are running:
   * If you are on a machine that cannot run Oracle Instant Client, follow the steps outlined in [With Docker](#with-docker).

      **Note**: As of this writing, Apple M1 Macs cannot run Oracle Instant Client.
   * If you are on a machine that can run Oracle Instant Client, follow the steps outlined in [Without Docker](#without-docker): 

#### With Docker

1. Run `make dependencies` to download the Oracle Instant Client from S3.

2. Run `make dist-dev` to build the Docker container image.

3. Run `make publish-dev` to push the Docker container image to ECR for the `Dev1` environment. 

4. Run any `make` commands for testing the application. In the Makefile, the make commands will be appended with '-dev' (e.g. `run-connection-tests-dev`).

#### Without Docker

1. Download [Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client/downloads.html) (basiclite is sufficient) and set the `ORACLE_LIB_DIR` env variable.

2. Run `pipenv run carbon`.

### Running the application as an ECS task

The application can be run as an ECS task. Any runs that require a connection to the Data Warehouse must be executed as a task in the `Stage-Workloads` environment because Cloudconnector is not enabled in `Dev1`. This requires building and publishing the Docker container image to ECR for `Stage-Workloads`.

1. Export AWS credentials for the `stage` environment. The `ECR_NAME_STAGE` and `ECR_URL_STAGE` environment variables must also be set. The values correspond to the 'Repository name' and 'URI' indicated on ECR for the container image, respectively.

2. Run `make dist-stage` to build the Docker container image.

3. Run `make publish-stage` to push the Docker container image to ECR for the `stage` environment.

4. Run any `make` commands with calls to `aws ecs run-task --cluster carbon-ecs-stage ...` for testing the application.

For an example, see [Connecting to the Data Warehouse](#connecting-to-the-data-warehouse).

## Deploying

In the AWS Organization, we have a automated pipeline from `Dev1` --> `Stage-Workloads` --> `Prod-Workloads`, handled by GitHub Actions.

### Staging

When a PR is merged onto the `main` branch, Github Actions will build a new container image. The container image will be tagged with "latest" and the shortened commit hash (the commit that merges the PR to `main`). The tagged image is then uploaded to the ECR repository in `Stage-Workloads`. An EventBridge scheduled event will periodically trigger the Fargate task to run. This task will use the latest image from the ECR registry.

### Production

Tagging a release on the `main` branch will promote a copy of the `latest` container from `Stage-Workloads` to `Prod-Workloads`.

## Connecting to the Data Warehouse

The password for the Data Warehouse is updated each year. To verify that the updated password works, run the connection tests for Carbon. Carbon will run connection tests for the Data Warehouse and the Elements FTP server when executed with the flag `--run_connection_tests`. 

1. Export AWS credentials for the `stage` environment. The `ECR_NAME_STAGE` and `ECR_URL_STAGE` environment variables must also be set. The values correspond to the 'Repository name' and 'URI' indicated on ECR for the container image, respectively.
2. Run `make install`.
3. Run `make run-connection-tests-stage`.
4. View the logs from the ECS task run on CloudWatch.
   * On CloudWatch, select the `carbon-ecs-stage` log group.
   * Select the most recent log stream.
   * Verify that the following log is included:
      > Successfully connected to the Data Warehouse: \<VERSION NUMBER\>

## Required ENV

* `FEED_TYPE` = The type of feed and is set to either "people" or "articles".
* `DATAWAREHOUSE_CLOUDCONNECTOR_JSON`: A JSON formatted collection of key/value pairs for the MIT Data Warehouse connection through CloudConnector. The key/value pairs are:
   * `USER`: The username for accessing the Data Warehouse database.
   * `PASSWORD`: The password for accessing the Data Warehouse database.
   * `HOST`: The host for the Data Warehouse database.
   * `PORT`: The port for accessing the Data Warehouse database.
   * `PATH`: The Oracle system identifier (SID) for the Data Warehouse database.
   * `CONNECTION_STRING` = The connection string of the form `oracle://<username>:<password>@<host>:1521/<sid>` for the Data Warehouse.
* `SNS_TOPIC` = The ARN for the SNS topic used for sending email notifications.
* `SYMPLECTIC_FTP_JSON`: A JSON formatted collection of key/value pairs for connecting to the Symplectic Elements FTP server.
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