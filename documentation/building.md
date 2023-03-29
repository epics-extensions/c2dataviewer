# Building and packaging

## Conda 

To build a conda package:
```bash
conda build . -c epics -c conda-forge
```

To install build package in a new environment:
```bash
conda create -n c2dv.0001 local::c2dataviewer
```

To run app from new environment:
```bash
source activate c2dv.0001
c2dv --app scope
```

## Pip

To install pip dependencies:
```bash
make pip-dependencies
```

To build a pip package:
```bash
make pip-build
```
To run the unit tests run:
```bash
make pip-test
```

To install package locally
```bash
python3 -m venv c2dv.0001
source c2dv.0001/bin/activate
pip install dist/c2dataviewer-*.tar.gz
```
