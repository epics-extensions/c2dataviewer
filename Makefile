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
	conda build .


.PHONY:conda-clean
conda-clean:
	rm -f setup.py
	conda build purge

.PHONY:conda-dependencies
conda-dependencies:
	conda install c2-tool

.PHONY:conda-upload
conda-upload: 
	conda create -n importenv local::c2dataviewer
	conda list -n importenv --explicit > importenv.txt
	conda activate
	c2 repo import -r /net/epics-ops/webroots_b/Public5/repo/docroot/c2/conda -c $CONDA_PREFIX  --package-list importenv.txt
	rm importenv.txt
	conda remove -n importenv --all

.PHONY:c2-env-update
c2-env-update: 
	c2 env checkout envs -n gui
	cd envs/gui
	c2 env resolve
	c2 env commit
	rm -rf envs

.PHONY:c2-env-deploy
c2-env-deploy: 
	c2 env checkout envs -n gui
	cd envs/gui
	umask 002
	c2 env deploy
	rm -rf envs

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
	cp -f setup_pip.py setup.py
	$(PYTHON) setup.py sdist bdist_wheel

.PHONY:pip-test
pip-test:
	tox

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
