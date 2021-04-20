DESTDIR     ?=
prefix      ?= $(DESTDIR)/usr
bindir      ?= $(prefix)/bin
datarootdir ?= $(prefix)/share
sharedir    ?= $(datarootdir)/base
docdir      ?= $(datarootdir)/doc/base
man1dir     ?= $(datarootdir)/man/man1

SHELL := bash

build:
.PHONY: build

install:
	@mkdir -p "$(bindir)"
	@install -m 0755 base.sh "$(bindir)/base"
	@install -m 0755 base_activate.sh "$(bindir)/base_activate"
	@mkdir -p "$(sharedir)"
	@install -m 0644 share/* "$(sharedir)"
	@mkdir -p "$(man1dir)"
	@install -m 0644 -T <(gzip -c doc/base.1) "$(man1dir)/base.1.gz"
	@mkdir -p "$(docdir)"
	@install -m 0644 -T <(gzip -c README.md) "$(docdir)/README.md.gz"
	@install -m 0644 -T <(gzip -c CHANGELOG.md) "$(docdir)/changelog.gz"
	@install -m 0644 -T <(gzip -c LICENSE) "$(docdir)/LICENSE.gz"
.PHONY: install

test:
.PHONY: test
