.PHONY: help install deps wheel clean distclean test lint coveralls \
				update dist-dev publish-dev dist-stage publish-stage

## ---- This is the Terraform-generated header for carbon-dev. ---- ## \
If this is a Lambda repo, uncomment the FUNCTION line below \
and review the other commented lines in the document. 
ECR_NAME_DEV:=carbon-dev
ECR_URL_DEV:=222053980223.dkr.ecr.us-east-1.amazonaws.com/carbon-dev
# FUNCTION_DEV:=
## ---- End of Terraform-generated header ---- ##

SHELL=/bin/bash
S3_BUCKET:=shared-files-$(shell aws sts get-caller-identity --query "Account" --output text)
ORACLE_ZIP:=instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip
DATETIME:=$(shell date -u +%Y%m%dT%H%M%SZ)

## ---- Dependency commands ---- ##

install: # install python dependencies
	pipenv install --dev

update: install # update all python dependencies
	pipenv clean
	pipenv update --dev

dependencies: # download Oracle instant client zip
	aws s3 cp s3://$(S3_BUCKET)/files/$(ORACLE_ZIP) vendor/$(ORACLE_ZIP)

## ---- Test commands ---- ##

test: # run tests and print coverage report
	pipenv run coverage run --source=carbon -m pytest -vv
	pipenv run coverage report -m

	
coveralls: test
	pipenv run coverage lcov -o ./coverage/lcov.info

## ---- Code quality and safety commands ---- ##

lint: black bandit mypy ruff safety 

bandit:
	pipenv run bandit -r carbon

black: 
	pipenv run black -l 90 --check --diff --color .

mypy: 
	pipenv run mypy carbon

ruff: 
	pipenv run ruff check .

safety:
	pipenv check
	pipenv verify

# apply changes to resolve any linting errors
lint-apply: black-apply

black-apply: 
	pipenv run black -l 90 .

## ---- Terraform-generated Developer Deploy Commands for Dev1 environment ---- ##

dist-dev: # build docker container (intended for developer-based manual build)
	docker build --platform linux/amd64 \
	    -t $(ECR_URL_DEV):latest \
		-t $(ECR_URL_DEV):`git describe --always` \
		-t $(ECR_NAME_DEV):latest .

publish-dev: dist-dev # build, tag and push (intended for developer-based manual publish)
	docker login -u AWS -p $$(aws ecr get-login-password --region us-east-1) $(ECR_URL_DEV)
	docker push $(ECR_URL_DEV):latest
	docker push $(ECR_URL_DEV):`git describe --always`

## ---- Terraform-generated manual shortcuts for deploying to Stage. ----  ## \
This requires that ECR_NAME_STAGE, ECR_URL_STAGE, and FUNCTION_STAGE environment \
variables are set locally by the developer and that the developer has \
authenticated to the correct AWS Account. The values for the environment \
variables can be found in the stage_build.yml caller workflow. \
While Stage should generally only be used in an emergency for most repos, \
it is necessary for any testing requiring access to the Data Warehouse \
because Cloud Connector is not enabled on Dev1.

dist-stage: 
	docker build --platform linux/amd64 \
	    -t $(ECR_URL_STAGE):latest \
		-t $(ECR_URL_STAGE):`git describe --always` \
		-t $(ECR_NAME_STAGE):latest .

 publish-stage:
	docker login -u AWS -p $$(aws ecr get-login-password --region us-east-1) $(ECR_URL_STAGE)
	docker push $(ECR_URL_STAGE):latest
	docker push $(ECR_URL_STAGE):`git describe --always`
