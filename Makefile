SHELL := /bin/bash

publish_pypi:
	rm -rf dist build
	python3 setup.py sdist bdist_wheel
	source .envrc-dev && twine upload -u $$PYPI_USERNAME -p $$PYPI_PASSWORD dist/*

