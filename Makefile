PREFIX := /usr/local

all: install

install:
	python3 -m pip install -r requirements.txt
	cp anicli-ru $(DESTDIR)$(PREFIX)/bin/anicli-ru
	chmod 0755 $(DESTDIR)$(PREFIX)/bin/anicli-ru
uninstall:
	$(RM) $(DESTDIR)$(PREFIX)/bin/anicli-ru


.PHONY: all install uninstall
