PREFIX := /usr/local

all: install

install:
	python3 -m pip install -r requirements.txt
	python3 setup.py install
	cp anicli.py $(DESTDIR)$(PREFIX)/bin/anicli-ru
	chmod 0755 $(DESTDIR)$(PREFIX)/bin/anicli-ru
uninstall:
	$(RM) $(DESTDIR)$(PREFIX)/bin/anicli-ru
	python3 -m pip uninstall anicli_ru


.PHONY: all install uninstall
