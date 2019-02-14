.PHONY: help install deps wheel container dist clean distclean test tests \
				update publish
SHELL=/bin/bash
S3_BUCKET=deploy-mitlib-stage
ORACLE_ZIP=instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip
ECR_REGISTRY=672626379771.dkr.ecr.us-east-1.amazonaws.com
DATETIME:=$(shell date -u +%Y%m%dT%H%M%SZ)

help: ## Print this message
	@awk 'BEGIN { FS = ":.*##"; print "Usage:  make <target>\n\nTargets:" } \
		/^[-_[:alpha:]]+:.?*##/ { printf "  %-15s%s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install python dependencies (runs `pipenv install`)
	pipenv install

vendor/$(ORACLE_ZIP):
	aws s3 cp s3://$(S3_BUCKET)/$(ORACLE_ZIP) vendor/$(ORACLE_ZIP)

deps: vendor/$(ORACLE_ZIP)

wheel:
	pipenv run python setup.py bdist_wheel

container:
	docker build -t $(ECR_REGISTRY)/carbon-stage:latest \
		-t $(ECR_REGISTRY)/carbon-stage:`git describe --always` \
		-t carbon .

dist: deps wheel container ## Build docker image
	@tput setaf 2
	@tput bold
	@echo "Finished building docker image. Try running:"
	@echo "  $$ docker run --rm carbon"
	@tput sgr0

clean: ## Remove build artifacts
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	find . -name '__pycache__' -print0 | xargs -0 rm -rf
	rm -rf .coverage .tox *.egg-info .eggs build/ dist/

distclean: clean ## Remove build artifacts and vendor libs
	rm -rf vendor/

test: ## Run tests
	tox

tests: test

update: ## Update all python dependencies
	pipenv clean
	pipenv update --dev

publish: ## Push and tag the latest image (use `make dist && make publish`)
	$$(aws ecr get-login --no-include-email --region us-east-1)
	docker push $(ECR_REGISTRY)/carbon-stage:latest
	docker push $(ECR_REGISTRY)/carbon-stage:`git describe --always`

promote: ## Promote the current staging build to production
	$$(aws ecr get-login --no-include-email --region us-east-1)
	docker pull $(ECR_REGISTRY)/carbon-stage:latest
	docker tag $(ECR_REGISTRY)/carbon-stage:latest $(ECR_REGISTRY)/carbon-prod:latest
	docker tag $(ECR_REGISTRY)/carbon-stage:latest $(ECR_REGISTRY)/carbon-prod:$(DATETIME)
	docker push $(ECR_REGISTRY)/carbon-prod:latest
	docker push $(ECR_REGISTRY)/carbon-prod:$(DATETIME)
