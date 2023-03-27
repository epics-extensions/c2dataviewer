# Building and packaging

## Building locally

Make sure to either use the [C2 conda installation](https://repo.aps.anl.gov/c2/install/) or add the following to your `$HOME/.condarc`
```yaml
channel_alias: https://repo.aps.anl.gov/c2/conda/
channels:
  - aps/c2
  - ext/pkgs/main
  - ext/conda-forge
  - ext/pkgs/free
```

To build a conda package:
```bash
make
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
## C2 Conda packaging
Below are steps to upload to the [C2 conda channel](https://repo.aps.anl.gov/c2/conda/aps/c2/).

To install dependencies:
```base
make conda-dependencies
```
To build package
```base
#must checkout a particular tag
git checkout 1.5.0
make conda-build
```

To upload the package:
```bash
make conda-upload
```

To update and deploy the c2 gui environment:
```base
#required fo environment to get latest changes
make c2-env-update

#deploys to /C2
make c2-env-deploy
```
