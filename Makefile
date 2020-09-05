help:
	@echo "Available Targets:"
	@cat Makefile | egrep '^(\w+?):' | sed 's/:\(.*\)//g' | sed 's/^/- /g'

test:
	@python -m pytest

release:
	@python setup.py sdist bdist_wheel
	@twine upload dist/*

lint:
	@flake8 .
	@isort .
	@pydocstyle .
	@black .

.PHONY: test release
