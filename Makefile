.PHONY: install test run lint

install:
\tpip install -e .

run:
\tbootstrap --config env/egeon.yaml

test:
\tpytest -q

lint:
\tpython -m py_compile $(shell find . -name "*.py")
