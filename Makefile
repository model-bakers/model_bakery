help:
	@echo "Available Targets:"
	@cat Makefile | egrep '^(\w+?):' | sed 's/:\(.*\)//g' | sed 's/^/- /g'

test:
	@python -m pytest

release:
	@python setup.py sdist bdist_wheel
	@twine upload dist/*

lint:
	@black model_bakery
	@flake8 model_bakery

.PHONY: test release
