DESTDIR ?=
prefix  ?= /usr

bindir      := $(DESTDIR)$(prefix)/bin
datarootdir := $(DESTDIR)$(prefix)/share
sharedir    := $(datarootdir)/base
docdir      := $(datarootdir)/doc/base
man1dir     := $(datarootdir)/man/man1

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
	@install -m 0644 doc/base.1 "$(man1dir)"
	@gzip "$(man1dir)/base.1"
	@mkdir -p "$(docdir)"
	@install -m 0644 README.md "$(docdir)"
	@gzip "$(docdir)/README.md"
	@install -m 0644 -T CHANGELOG.md "$(docdir)/changelog"
	@gzip "$(docdir)/changelog"
	@install -m 0644 LICENSE "$(docdir)"
	@gzip "$(docdir)/LICENSE"
.PHONY: install

test:
.PHONY: test
