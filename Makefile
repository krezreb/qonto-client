SHELL := /bin/bash

publish_pypi:
	rm -rf dist build
	python3 setup.py sdist bdist_wheel
	source .envrc-dev && twine upload -u $$PYPI_USERNAME -p $$PYPI_PASSWORD dist/*

last_month_ofx:
	python3 export_ofx.py --last-month --zip --attachments --dir export/last_month