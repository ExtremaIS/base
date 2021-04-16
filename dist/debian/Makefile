prefix      ?= /usr
bindir      ?= $(prefix)/bin
datarootdir ?= $(prefix)/share
sharedir    ?= $(datarootdir)/base
docdir      ?= $(datarootdir)/doc/base
man1dir     ?= $(datarootdir)/man/man1

SHELL := bash

build:
	@echo "nothing to do"
.PHONY: build

install:
	@mkdir -p $(DESTDIR)$(bindir)
	@install -m 0755 base.sh $(DESTDIR)$(bindir)/base
	@install -m 0755 base_activate.sh $(DESTDIR)$(bindir)/base_activate
	@mkdir -p $(DESTDIR)$(sharedir)
	@install -m 0644 share/* $(DESTDIR)$(sharedir)
	@mkdir -p $(DESTDIR)$(man1dir)
	@install -m 0644 -T <(gzip -c doc/base.1) $(DESTDIR)$(man1dir)/base.1.gz
	@mkdir -p $(DESTDIR)$(docdir)
	@install -m 0644 -T <(gzip -c README.md) $(DESTDIR)$(docdir)/README.md.gz
	@install -m 0644 -T <(gzip -c CHANGELOG.md) \
		$(DESTDIR)$(docdir)/changelog.gz
	@install -m 0644 -T <(gzip -c LICENSE) $(DESTDIR)$(docdir)/LICENSE.gz
.PHONY: install

test:
	@echo "nothing to do"
.PHONY: test
