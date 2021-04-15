##############################################################################
# Project configuration

DOCKER_IMAGE := extremais/basetest

##############################################################################
# Make configuration

ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error GNU Make 4.0 or later required)
endif
.RECIPEPREFIX := >

SHELL := bash
.SHELLFLAGS := -o nounset -o errexit -o pipefail -c

MAKEFLAGS += --no-builtin-rules
MAKEFLAGS += --warn-undefined-variables

.DEFAULT_GOAL := help

##############################################################################
# Rules

#deb: TODO

#doc: TODO

#clean: TODO

help: # show this help
> @grep '^[a-zA-Z0-9._-]\+:[^#]*# ' $(MAKEFILE_LIST) \
>   | sed 's/^\([^:]\+\):[^#]*# \(.*\)/make \1\t\2/' \
>   | column -t -s $$'\t'
.PHONY: help

hr: #internal# display a horizontal rule
> @command -v hr >/dev/null 2>&1 && hr -t || true
.PHONY: hr

lint: hr
lint: shellcheck
lint: pycodestyle
lint: pylint
lint: # run shellcheck, pycodestyle, and pylint
.PHONY: lint

man: # build man page
> $(eval VERSION := $(shell ./base.sh --version | sed 's/base //'))
> $(eval DATE := $(shell date --rfc-3339=date))
> @mkdir -p build
> @pandoc -s -t man -o build/base.1 \
>   --variable header="Base Manual" \
>   --variable footer="Base $(VERSION) ($(DATE))" \
>   doc/base.1.md
.PHONY: man

pycodestyle: hr
pycodestyle: # run pycodestyle on basetest.py
> @if command -v pycodestyle >/dev/null 2>&1; \
>   then pycodestyle test/basetest.py; \
>   else echo "WARNING: pycodestyle not found; skipping"; \
>   fi
.PHONY: pycodestyle

pylint: hr
pylint: # run pylint on basetest.py
> @if command -v pylint >/dev/null 2>&1; \
>   then pylint test/basetest.py; \
>   else echo "WARNING: pylint not found; skipping"; \
>   fi
.PHONY: pylint

#recent: TODO

#rpm: TODO

shellcheck: hr
shellcheck: # run shellcheck on base
> @if command -v shellcheck >/dev/null 2>&1; \
>   then find . -type f -name '*.sh' | xargs shellcheck; \
>   else echo "WARNING: shellcheck not found; skipping"; \
>   fi
.PHONY: shellcheck

#source-git: TODO

#source-tar: TODO

test: hr
test: test-image
test: # run all tests or test T in test container
> $(eval T := "")
> @test -z "$(T)" \
>   && docker run --rm -it \
>       --hostname "basetest" \
>       -v "$(PWD)/base.sh:/usr/bin/base:ro" \
>       -v "$(PWD)/base_activate.sh:/usr/bin/base_activate:ro" \
>       -v "$(PWD)/share:/usr/share/base:ro" \
>       -v "$(PWD)/test/basetest.py:/home/docker/basetest:ro" \
>       "$(DOCKER_IMAGE):latest" \
>       /home/docker/basetest \
>   || docker run --rm -it \
>       --hostname "basetest" \
>       -v "$(PWD)/base.sh:/usr/bin/base:ro" \
>       -v "$(PWD)/base_activate.sh:/usr/bin/base_activate:ro" \
>       -v "$(PWD)/share:/usr/share/base:ro" \
>       -v "$(PWD)/test/basetest.py:/home/docker/basetest:ro" \
>       "$(DOCKER_IMAGE):latest" \
>       /home/docker/basetest "TestBase.$(T)"
.PHONY: test

test-image: # build test image
> $(eval EXISTS := $(shell docker images --quiet $(DOCKER_IMAGE):latest))
> @test -n "$(EXISTS)" || docker build \
>   --build-arg "TERM=${TERM}" \
>   --tag "$(DOCKER_IMAGE):latest" \
>   test
.PHONY: test-image

test-shell: test-image
test-shell: # run shell in test container
> @docker run --rm -it \
>   --hostname "basetest" \
>   -v "$(PWD)/base.sh:/usr/bin/base:ro" \
>   -v "$(PWD)/base_activate.sh:/usr/bin/base_activate:ro" \
>   -v "$(PWD)/share:/usr/share/base:ro" \
>   -v "$(PWD)/test/basetest.py:/home/docker/basetest:ro" \
>   "$(DOCKER_IMAGE):latest" \
>   /bin/bash
.PHONY: test-shell

#todo: TODO

version: # show current version
> @./base.sh --version
.PHONY: version
