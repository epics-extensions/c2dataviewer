TOP = .

PYTHON = python3

.PHONY:all
all: conda

.PHONY:clean
clean: conda-clean pip-clean

.PHONY:conda
conda: conda-build

.PHONY:conda-build
conda-build:
	cp -f setup_conda.py setup.py
	conda build . -c epics

.PHONY:conda-install
conda-install:
	conda install -c local -c epics c2dataviewer

.PHONY:conda-clean
conda-clean:

.PHONY:pip
pip: pip-build pip-test

.PHONY:pip-dependencies
pip-dependencies:
	$(PYTHON) -m pip install --upgrade setuptools wheel
	$(PYTHON) -m pip install --upgrade twine
	$(PYTHON) -m pip install --upgrade tox

.PHONY:pip-build
pip-build:
	cp -f setup_pip.py setup.py
	$(PYTHON) setup.py sdist bdist_wheel

.PHONY:pip-test
pip-test:
	tox

.PHONY:pip-upload
pip-upload:
	rm -f dist/*dirty*
	$(PYTHON) -m twine upload dist/*

.PHONY:pip-clean
pip-clean:
	rm -rf setup.py
	rm -rf .eggs
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	rm -rf .tox
