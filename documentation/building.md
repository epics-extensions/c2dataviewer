# Building and packaging

## Building locally

**NOTE** : *c2dv* currently require *pyqtgraph* version `0.10.0`. There is an unresolved issue with the
newer version(s): https://git.aps.anl.gov/C2/conda/data-viewer/-/issues/48.
Correct version of the *pyqtgraph* should be installed manually.


To build a conda package:
```bash
make
```

To install build package in a new environment:
```bash
conda create -n c2dv.0001 pyqtgraph=0.10.0 local::c2dataviewer -c epics
```

To run app from new environment:
```bash
source activate c2dv.0001
c2dv --app scope
```

## Pip Packaging

To install pip dependencies:
```bash
make pip-dependencies
```

To build a pip package:
```bash
# must checkout a particular tag
git checkout 1.5.0
make pip-build
```
To run the unit tests run:
```bash
make pip-test
```

To upload the package on PyPI:
```bash
make pip-upload
```

