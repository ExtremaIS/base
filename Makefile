##############################################################################
# Project configuration

PROJECT        := base
TEST_CONTAINER := extremais/basetest

DESTDIR ?=
PREFIX  ?= /usr/local

DEB_CONTAINER    ?= extremais/pkg-debian:bullseye
RPM_CONTAINER    ?= extremais/pkg-fedora:34
MAINTAINER_NAME  ?= Travis Cardwell
MAINTAINER_EMAIL ?= travis.cardwell@extrema.is

TEST_DEB_CONTAINER ?= debian:bullseye
TEST_DEB_ARCH      ?= all
TEST_RPM_CONTAINER ?= fedora:34
TEST_RPM_OS        ?= fc34
TEST_RPM_ARCH      ?= noarch

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

BINDIR      := $(DESTDIR)$(PREFIX)/bin
DATAROOTDIR := $(DESTDIR)$(PREFIX)/share
SHAREDIR    := $(DATAROOTDIR)/$(PROJECT)
DOCDIR      := $(DATAROOTDIR)/doc/$(PROJECT)
MAN1DIR     := $(DATAROOTDIR)/man/man1

##############################################################################
# Functions

define all_files
  find . -not -path '*/\.*' -type f
endef

define checksum_files
  find . -maxdepth 1 -type f -not -path './*SUMS' | sed 's,^\./,,' | sort
endef

define die
  (echo "error: $(1)" ; false)
endef

define get_version
$(shell grep ^BASE_VERSION $(if $(origin 1) == undefined,base.sh,$(1)) \
        | sed -e 's/^[^"]*"//' -e 's/"$$//')
endef

##############################################################################
# Rules

checksums: # calculate checksums of build artifacts
> @cd build && $(call checksum_files) | xargs md5sum > MD5SUMS
> @cd build && $(call checksum_files) | xargs sha1sum > SHA1SUMS
> @cd build && $(call checksum_files) | xargs sha256sum > SHA256SUMS
> @cd build && $(call checksum_files) | xargs sha512sum > SHA512SUMS
.PHONY: checksums

clean: # clean package
.PHONY: clean

clean-all: clean
clean-all: # clean package and remove artifacts
> @rm -rf build
.PHONY: clean-all

deb: # build .deb package for VERSION in a Debian container
> $(eval VERSION := $(call get_version))
> $(eval SRC := $(PROJECT)-$(VERSION).tar.xz)
> @test -f build/$(SRC) || $(call die,"build/$(SRC) not found")
> @docker run --rm -it \
>   -e DEBFULLNAME="$(MAINTAINER_NAME)" \
>   -e DEBEMAIL="$(MAINTAINER_EMAIL)" \
>   -v $(PWD)/build:/host \
>   $(DEB_CONTAINER) \
>   /home/docker/bin/make-deb.sh "$(SRC)"
.PHONY: deb

deb-test: # run a Debian container to test .deb package for VERSION
> $(eval VERSION := $(call get_version))
> $(eval PKG := "$(PROJECT)_$(VERSION)-1_$(TEST_DEB_ARCH).deb")
> @test -f build/$(PKG) || $(call die,"build/$(PKG) not found")
> @docker run --rm -it \
>   -v $(PWD)/build/$(PKG):/tmp/$(PKG):ro \
>   $(TEST_DEB_CONTAINER) \
>   /bin/bash
.PHONY: deb-test

doc: # build script documentation
> $(eval VERSION := $(call get_version))
> @mkdir -p build
> @literatex --ignore-shebang \
>   --input base.sh --output build/base-$(VERSION).md
> @pandoc \
>   --from markdown --to html5 --standalone \
>   --metadata title="base $(VERSION)" \
>   --output build/base-$(VERSION).html \
>   build/base-$(VERSION).md
> @literatex --ignore-shebang \
>   --input base_activate.sh --output build/base_activate-$(VERSION).md
> @pandoc \
>   --from markdown --to html5 --standalone \
>   --metadata title="base $(VERSION)" \
>   --output build/base_activate-$(VERSION).html \
>   build/base_activate-$(VERSION).md
.PHONY: doc

grep: # grep all non-hidden files for expression E
> $(eval E:= "")
> @test -n "$(E)" || $(call die,"usage: make grep E=expression")
> @$(call all_files) | xargs grep -Hn '$(E)' || true
.PHONY: grep

help: # show this help
> @grep '^[a-zA-Z0-9_-]\+:[^#]*# ' $(MAKEFILE_LIST) \
>   | sed 's/^\([^:]\+\):[^#]*# \(.*\)/make \1\t\2/' \
>   | column -t -s $$'\t'
.PHONY: help

hr: #internal# display a horizontal rule
> @command -v hr >/dev/null 2>&1 && hr -t || true
.PHONY: hr

ignored: # list files ignored by git
> @git ls-files . --ignored --exclude-standard --others
.PHONY: ignored

install: install-bin
install: install-share
install: install-man
install: install-doc
install: # install everything
.PHONY: install

install-bin: # install scripts
> @mkdir -p "$(BINDIR)"
> @install -m 0755 base.sh "$(BINDIR)/base"
> @install -m 0755 base_activate.sh "$(BINDIR)/base_activate"
.PHONY: install-bin

install-doc: # install documentation
> @mkdir -p "$(DOCDIR)"
> @install -m 0644 README.md "$(DOCDIR)"
> @gzip "$(DOCDIR)/README.md"
> @install -m 0644 -T CHANGELOG.md "$(DOCDIR)/changelog"
> @gzip "$(DOCDIR)/changelog"
> @install -m 0644 LICENSE "$(DOCDIR)"
> @gzip "$(DOCDIR)/LICENSE"
.PHONY: install-doc

install-man: # install man page
> @mkdir -p "$(MAN1DIR)"
> @install -m 0644 doc/base.1 "$(MAN1DIR)"
> @gzip "$(MAN1DIR)/base.1"
.PHONY: install-man

install-share: # install share scripts
> @mkdir -p "$(SHAREDIR)"
> @install -m 0644 share/* "$(SHAREDIR)"
.PHONY: install-share

lint: hr
lint: shellcheck
lint: pycodestyle
lint: pylint
lint: # run shellcheck, pycodestyle, and pylint
.PHONY: lint

man: # build man page
> $(eval VERSION := $(call get_version))
> $(eval DATE := $(shell date --rfc-3339=date))
> @pandoc -s -t man -o doc/base.1 \
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

recent: # show N most recently modified files
> $(eval N := "10")
> @find . -not -path '*/\.*' -type f -printf '%T+ %p\n' \
>   | sort --reverse \
>   | head -n $(N)
.PHONY: recent

rpm: # build .rpm package for VERSION in a Fedora container
> $(eval VERSION := $(call get_version))
> $(eval SRC := $(PROJECT)-$(VERSION).tar.xz)
> @test -f build/$(SRC) || $(call die,"build/$(SRC) not found")
> @docker run --rm -it \
>   -e RPMFULLNAME="$(MAINTAINER_NAME)" \
>   -e RPMEMAIL="$(MAINTAINER_EMAIL)" \
>   -v $(PWD)/build:/host \
>   $(RPM_CONTAINER) \
>   /home/docker/bin/make-rpm.sh "$(SRC)"
.PHONY: rpm

rpm-test: # run a Fedora container to test .rpm package for VERSION
> $(eval VERSION := $(call get_version))
> $(eval PKG := "$(PROJECT)-$(VERSION)-1.$(TEST_RPM_OS).$(TEST_RPM_ARCH).rpm")
> @test -f build/$(PKG) || $(call die,"build/$(PKG) not found")
> @docker run --rm -it \
>   -v $(PWD)/build/$(PKG):/tmp/$(PKG):ro \
>   $(TEST_RPM_CONTAINER) \
>   /bin/bash
.PHONY: rpm-test

shellcheck: hr
shellcheck: # run shellcheck on all shell scripts
> @if command -v shellcheck >/dev/null 2>&1; \
>   then find . -type f -name '*.sh' | xargs shellcheck; \
>   else echo "WARNING: shellcheck not found; skipping"; \
>   fi
.PHONY: shellcheck

source-git: # create source tarball of git TREE
> $(eval TREE := "HEAD")
> $(eval BRANCH := $(shell git rev-parse --abbrev-ref $(TREE)))
> @test "$(BRANCH)" = "main" || echo "WARNING: Not in main branch!" >&2
> $(eval DIRTY := $(shell git diff --shortstat | wc -l))
> @test "$(DIRTY)" = "0" \
>   || echo "WARNING: Not including non-committed changes!" >&2
> $(eval UNTRACKED := $(shell \
    git ls-files --other --directory --no-empty-directory --exclude-standard \
    | wc -l))
> @test "$(UNTRACKED)" = "0" \
>   || echo "WARNING: Not including untracked files!" >&2
> $(eval VERSION := $(call get_version))
> @mkdir -p build
> @git archive --format=tar --prefix=$(PROJECT)-$(VERSION)/ $(TREE) \
>   | xz \
>   > build/$(PROJECT)-$(VERSION).tar.xz
.PHONY: source-git

source-tar: # create source tarball using tar
> $(eval DIRTY := $(shell git diff --shortstat | wc -l))
> @test "$(DIRTY)" = "0" \
>   || echo "WARNING: Including non-committed changes!" >&2
> $(eval UNTRACKED := $(shell \
    git ls-files --other --directory --no-empty-directory --exclude-standard \
    | wc -l))
> @test "$(UNTRACKED)" = "0" \
>   || echo "WARNING: Including untracked files!" >&2
> $(eval VERSION := $(call get_version))
> @mkdir -p build
> @sed -e 's,^/,./,' -e 's,/$$,,' .gitignore > build/.gitignore
> @tar \
>   --exclude-vcs \
>   --exclude-ignore-recursive=build/.gitignore \
>   --transform "s,^\.,$(PROJECT)-$(VERSION)," \
>   -Jcf build/$(PROJECT)-$(VERSION).tar.xz \
>   .
> @rm -f build/.gitignore
.PHONY: source-tar

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
>       "$(TEST_CONTAINER):latest" \
>       /home/docker/basetest \
>   || docker run --rm -it \
>       --hostname "basetest" \
>       -v "$(PWD)/base.sh:/usr/bin/base:ro" \
>       -v "$(PWD)/base_activate.sh:/usr/bin/base_activate:ro" \
>       -v "$(PWD)/share:/usr/share/base:ro" \
>       -v "$(PWD)/test/basetest.py:/home/docker/basetest:ro" \
>       "$(TEST_CONTAINER):latest" \
>       /home/docker/basetest "TestBase.$(T)"
.PHONY: test

test-image: # build test image
> $(eval EXISTS := $(shell docker images --quiet $(TEST_CONTAINER):latest))
> @test -n "$(EXISTS)" || docker build \
>   --build-arg "TERM=${TERM}" \
>   --tag "$(TEST_CONTAINER):latest" \
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
>   "$(TEST_CONTAINER):latest" \
>   /bin/bash
.PHONY: test-shell

todo: # search for TODO items
> @find . -type f \
>   -not -path '*/\.*' \
>   -not -path './build/*' \
>   -not -path './project/*' \
>   -not -path ./Makefile \
>   | xargs grep -Hn TODO \
>   | grep -v '^Binary file ' \
>   || true
.PHONY: todo

version: # show current version
> @echo "base.sh          $(call get_version, base.sh)"
> @echo "base_activate.sh $(call get_version, base_activate.sh)"
.PHONY: version
