VENV := venv
PYTHON := $(VENV)/bin/python


$(PYTHON):
	virtualenv $(VENV) --python python3.9
	$(PYTHON) -m pip install --upgrade pip build twine

requirements.txt: install
	$(PYTHON) -m pip freeze > requirements.txt

.PHONY: install
install: $(PYTHON)
	$(PYTHON) -m pip install --editable .[dev]

.PHONY: pre-commit
pre-commit:
	pre-commit run --all-files

.PHONY: build
build: $(PYTHON)
	rm -fr build/* dist/*
	$(PYTHON) -m build .

.PHONY: clean
clean:
	rm -fr build dist $(VENV) *.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

.PHONY: publish
publish: install build
	git checkout origin/main
	git pull origin main
	git tag -m "v$(VERSION)" v$(VERSION)
	git push --tags
	$(PYTHON) -m twine upload -u __token__ dist/*
