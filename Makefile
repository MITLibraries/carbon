.PHONY: help install deps wheel clean distclean test lint coveralls \
				update dist-dev publish-dev dist-stage publish-stage

### This is the Terraform-generated header for carbon-dev. If    ###
###   this is a Lambda repo, uncomment the FUNCTION line below   ###
###   and review the other commented lines in the document.      ###
ECR_NAME_DEV:=carbon-dev
ECR_URL_DEV:=222053980223.dkr.ecr.us-east-1.amazonaws.com/carbon-dev
# FUNCTION_DEV:=
### End of Terraform-generated header                            ###

SHELL=/bin/bash
S3_BUCKET:=shared-files-$(shell aws sts get-caller-identity --query "Account" --output text)
ORACLE_ZIP:=instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip
DATETIME:=$(shell date -u +%Y%m%dT%H%M%SZ)

help: ## Print this message
	@awk 'BEGIN { FS = ":.*##"; print "Usage:  make <target>\n\nTargets:" } \
		/^[-_[:alpha:]]+:.?*##/ { printf "  %-15s%s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install python dependencies
	pipenv install --dev

dependencies: 
	aws s3 cp s3://$(S3_BUCKET)/files/$(ORACLE_ZIP) vendor/$(ORACLE_ZIP)

vendor/$(ORACLE_ZIP):
	aws s3 cp s3://$(S3_BUCKET)/files/$(ORACLE_ZIP) vendor/$(ORACLE_ZIP)

deps: vendor/$(ORACLE_ZIP) wheel

wheel:
	pipenv run python setup.py bdist_wheel

clean: ## Remove build artifacts
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	find . -name '__pycache__' -print0 | xargs -0 rm -rf
	rm -rf .coverage .tox *.egg-info .eggs build/ dist/

distclean: clean ## Remove build artifacts and vendor libs
	rm -rf vendor/

test: ## Run tests
	pipenv run coverage run --source=carbon -m pytest -vv
	pipenv run coverage report -m
	
coveralls: test
	pipenv run coveralls

lint: ## Run linters
	pipenv run flake8 carbon

update: ## Update all python dependencies
	pipenv clean
	pipenv update --dev

### Terraform-generated Developer Deploy Commands for Dev environment    ###
dist-dev: ## Build docker container (intended for developer-based manual build)
	docker build --platform linux/amd64 \
	    -t $(ECR_URL_DEV):latest \
		-t $(ECR_URL_DEV):`git describe --always` \
		-t $(ECR_NAME_DEV):latest .

publish-dev: dist-dev ## Build, tag and push (intended for developer-based manual publish)
	docker login -u AWS -p $$(aws ecr get-login-password --region us-east-1) $(ECR_URL_DEV)
	docker push $(ECR_URL_DEV):latest
	docker push $(ECR_URL_DEV):`git describe --always`

### Terraform-generated manual shortcuts for deploying to Stage. This requires  ###
###   that ECR_NAME_STAGE, ECR_URL_STAGE, and FUNCTION_STAGE environment        ###
###   variables are set locally by the developer and that the developer has     ###
###   authenticated to the correct AWS Account. The values for the environment  ###
###   variables can be found in the stage_build.yml caller workflow.            ###
dist-stage: ## Only use in an emergency
	docker build --platform linux/amd64 \
	    -t $(ECR_URL_STAGE):latest \
		-t $(ECR_URL_STAGE):`git describe --always` \
		-t $(ECR_NAME_STAGE):latest .

publish-stage: ## Only use in an emergency
	docker login -u AWS -p $$(aws ecr get-login-password --region us-east-1) $(ECR_URL_STAGE)
	docker push $(ECR_URL_STAGE):latest
	docker push $(ECR_URL_STAGE):`git describe --always`
