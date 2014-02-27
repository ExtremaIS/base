prefix      ?= /usr/local
bindir      ?= $(prefix)/bin
datarootdir ?= $(prefix)/share
docdir      ?= $(datarootdir)/doc/base
mandir      ?= $(datarootdir)/man
man1dir     ?= $(mandir)/man1

none:
	@echo "make install    install to system"

install:
	mkdir -p $(DESTDIR)$(bindir)
	install -m 755 base.sh $(DESTDIR)$(bindir)/base
	mkdir -p $(DESTDIR)$(datarootdir)
	install -m 644 share/go.sh $(DESTDIR)$(datarootdir)/go.sh
	install -m 644 share/haskell.sh $(DESTDIR)$(datarootdir)/haskell.sh
	install -m 644 share/python.sh $(DESTDIR)$(datarootdir)/python.sh
	mkdir -p $(DESTDIR)$(man1dir)
	install -m 644 man/base.1 $(DESTDIR)$(man1dir)/base.1
	mkdir -p $(DESTDIR)$(docdir)
	install -m 644 README.md Changelog $(DESTDIR)$(docdir)

.PHONY: none install
