.PHONY: help install deps wheel container dist clean distclean test \
				update publish

### This is the Terraform-generated header for carbon-dev ###
ECR_NAME_DEV:=carbon-dev
ECR_URL_DEV:=222053980223.dkr.ecr.us-east-1.amazonaws.com/carbon-dev
### End of Terraform-generated header ###

SHELL=/bin/bash
S3_BUCKET=shared-files-222053980223
ORACLE_ZIP=instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip
ECR_REGISTRY=672626379771.dkr.ecr.us-east-1.amazonaws.com
DATETIME:=$(shell date -u +%Y%m%dT%H%M%SZ)

help: ## Print this message
	@awk 'BEGIN { FS = ":.*##"; print "Usage:  make <target>\n\nTargets:" } \
		/^[-_[:alpha:]]+:.?*##/ { printf "  %-15s%s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install python dependencies
	pipenv install --dev

vendor/$(ORACLE_ZIP):
	aws s3 cp s3://$(S3_BUCKET)/files/$(ORACLE_ZIP) vendor/$(ORACLE_ZIP)

deps: vendor/$(ORACLE_ZIP)

wheel:
	pipenv run python setup.py bdist_wheel

clean: ## Remove build artifacts
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	find . -name '__pycache__' -print0 | xargs -0 rm -rf
	rm -rf .coverage .tox *.egg-info .eggs build/ dist/

distclean: clean ## Remove build artifacts and vendor libs
	rm -rf vendor/

test: ## Run tests
	pipenv run pytest --cov=carbon

coveralls: test
	pipenv run coveralls

lint: ## Run linters
	pipenv run flake8 carbon

update: ## Update all python dependencies
	pipenv clean
	pipenv update --dev

publish: ## Push and tag the latest image (use `make dist && make publish`)
	aws ecr get-login-password --region us-east-1 | docker login \
    --username AWS \
    --password-stdin $(ECR_REGISTRY)
	docker push $(ECR_REGISTRY)/carbon-stage:latest
	docker push $(ECR_REGISTRY)/carbon-stage:`git describe --always`

promote: ## Promote the current staging build to production
	aws ecr get-login-password --region us-east-1 | docker login \
    --username AWS \
    --password-stdin $(ECR_REGISTRY)
	docker pull $(ECR_REGISTRY)/carbon-stage:latest
	docker tag $(ECR_REGISTRY)/carbon-stage:latest $(ECR_REGISTRY)/carbon-prod:latest
	docker tag $(ECR_REGISTRY)/carbon-stage:latest $(ECR_REGISTRY)/carbon-prod:$(DATETIME)
	docker push $(ECR_REGISTRY)/carbon-prod:latest
	docker push $(ECR_REGISTRY)/carbon-prod:$(DATETIME)


### Terraform-generated Developer Deploy Commands for Dev environment ###
dist-dev: deps wheel ## Build docker container (intended for developer-based manual build)
	docker build --platform linux/amd64 \
	    -t $(ECR_URL_DEV):latest \
		-t $(ECR_URL_DEV):`git describe --always` \
		-t $(ECR_NAME_DEV):latest .

publish-dev: dist-dev ## Build, tag and push (intended for developer-based manual publish)
	docker login -u AWS -p $$(aws ecr get-login-password --region us-east-1) $(ECR_URL_DEV)
	docker push $(ECR_URL_DEV):latest
	docker push $(ECR_URL_DEV):`git describe --always`

### Terraform-generated manual shortcuts for deploying to Stage ###
### This requires that ECR_NAME_STAGE & ECR_URL_STAGE environment variables are set locally
### by the developer and that the developer has authenticated to the correct AWS Account.
### The values for the environment variables can be found in the stage_build.yml caller workflow.
dist-stage: deps wheel ## Only use in an emergency
	docker build --platform linux/amd64 \
	    -t $(ECR_URL_STAGE):latest \
		-t $(ECR_URL_STAGE):`git describe --always` \
		-t $(ECR_NAME_STAGE):latest .

publish-stage: dist-stage ## Only use in an emergency
	docker login -u AWS -p $$(aws ecr get-login-password --region us-east-1) $(ECR_URL_STAGE)
	docker push $(ECR_URL_STAGE):latest
	docker push $(ECR_URL_STAGE):`git describe --always`
