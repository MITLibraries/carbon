.PHONY: install deps wheel container dist clean test tests update
SHELL=/bin/bash
S3_BUCKET=carbon-deploy
LIBAIO_SO=libaio.so.1.0.1
ORACLE_ZIP=instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip

install:
	pipenv install

vendor/$(ORACLE_ZIP):
	aws s3 cp s3://$(S3_BUCKET)/$(ORACLE_ZIP) vendor/$(ORACLE_ZIP)

deps: vendor/$(ORACLE_ZIP)

wheel:
	pipenv run python setup.py bdist_wheel

container:
	docker build -t carbon:`git describe --always` -t carbon:latest .

dist: deps wheel container
	@tput setaf 2
	@tput bold
	@echo "Finished building docker image. Try running:"
	@echo "  $$ docker run --rm carbon:`git describe --always`"
	@tput sgr0

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	find . -name '__pycache__' -print0 | xargs -0 rm -rf
	rm -rf .coverage .tox *.egg-info .eggs build/ dist/

distclean: clean
	rm -rf vendor/

test:
	tox

tests: test

update:
	pipenv clean
	pipenv update --dev
