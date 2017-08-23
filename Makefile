.PHONY: all clean install release test tests update
SHELL=/bin/bash
RELEASE_TYPE=patch

all: test

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	find . -name '__pycache__' -print0 | xargs -0 rm -rf
	rm -rf .coverage .tox *.egg-info .eggs

install:
	pipenv install

test:
	tox

tests: test

release:
	bumpversion $(RELEASE_TYPE)
	@tput setaf 2
	@echo Built release for `git describe --tag`. Make sure to run:
	@echo "  $$ git push origin `git rev-parse --abbrev-ref HEAD` tag `git describe --tag`"
	@tput sgr0

update:
	pipenv update --dev
	pipenv lock -r > requirements.txt
