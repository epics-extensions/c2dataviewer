<p align="center">
  <h1 align="center">C2DataViewer: EPICS7 pvObject Data Viewer</h1>
</p>

C2DataViewer is a Python based data viewer for next generation of APS control system (C2).
It is developed with pyqtgraph, PyQt, and uses pvaPy as pvAccess Python binding.
This is a viewer for pvData structured data objects as transported by pvAccess. Some use cases are a 'scope viewer',
and Area Detector images from the AD pva plugin.

# Download
```bash
> python -m pip install c2dataviewer
> c2dv -h
```

# Applications

- [Image app](documentation/imageapp.md) - displays Area detector images from the AD pva plugin
- [Scope app](documentation/scopeapp.md) - plots pvAccess waveform data
- [Striptool](documentation/striptool.md) - plots channel access and pvAccess scalar data

# Other documentation

- [Building and packaging](documentation/building.md)
