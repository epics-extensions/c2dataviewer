TOP = .

PYTHON = python3

.PHONY:clean
clean: conda-clean pip-clean

.PHONY:conda
conda: conda-build

.PHONY:conda-build
conda-build:	
	cp setup_conda.py setup.py
	conda build . -c epics -c conda-forge

.PHONY:conda-clean
conda-clean:
	conda build purge


.PHONY:pip
pip: pip-build pip-test

.PHONY:pip-dependencies
pip-dependencies:
	$(PYTHON) -m pip install --upgrade setuptools wheel
	$(PYTHON) -m pip install --upgrade twine
	$(PYTHON) -m pip install --upgrade tox

.PHONY:pip-build
pip-build:
	rm -f dist/*
	$(PYTHON) setup_pip.py sdist bdist_wheel

.PHONY:pip-test
pip-test:
	cp setup_pip.py setup.py
	tox
	rm setup.py

.PHONY:pip-upload
pip-upload:
	$(PYTHON) -m twine upload dist/*

.PHONY:pip-clean
pip-clean:
	rm -rf setup.py
	rm -rf .eggs
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	rm -rf .tox
