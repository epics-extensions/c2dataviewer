
<p align="center">
  <h1 align="center">C2DataViewer: EPICS7 pvObject Data Viewer</h1>
</p>

C2DataViewer is a Python based data viewer for next generation of APS control system (C2).
It is developed with pyqtgraph, PyQt, and uses pvaPy as pvAccess Python binding.
This is a viewer for pvData structured data objects as transported by pvAccess. Some use cases are a 'scope viewer',
and Area Detector images from the AD pva plugin.

# Conda Packaging

To build a conda package:
```bash
conda build . -c default -c epics -c conda-forge
```

To install build package in a new environment:
```bash
conda create -n c2dv.0001 local::c2dataviewer -c default -c epics -c conda-forge
```

To run app from new environment:
```bash
source activate c2dv.0001
c2dv --app scope
```
