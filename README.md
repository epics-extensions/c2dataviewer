<p align="center">
  <h1 align="center">C2DataViewer: EPICS7 pvObject Data Viewer</h1>
</p>

C2DataViewer is a Python based data viewer for next generation of APS control system (C2).
It is developed with pyqtgraph, PyQt, and uses pvaPy as pvAccess Python binding.
This is a viewer for pvData structured data objects as transported by pvAccess. Some use cases are a 'scope viewer',
and Area Detector images from the AD pva plugin.

# Quick Start

To build a conda package:
```bash
make
```

To install build package in a new environment:
```bash
conda create -n c2dv.0001 local::c2dataviewer -c epics
```

To run app from new environment:
```bash
source activate c2dv.0001
c2dv --app scope
```

# Image Application
Image application displays images from an areaDetector pvAccess channel.  To start:
```bash
c2dv --app image --pv <CHANNELNAME>
```
## Image Adjustment
Image display can be adjusted by setting the black and white points.  "Auto" button automatically adjusts the black and white points to the minimum and maximum values in the image.  
Minimum and maximum values of the black and white points can be set throught the Image Levels Adjustment "Adjust limits" window.

## Statistics
Along with the image, the following statistics are displayed:

- *Input type* - image data type
- *Runtime* - total time data viewer has been running
- *Frames* - total number of images viewer has processed
- *Max/Min* - maximum and minimum values in the image
- *Dead* - number of pixels that exceed the dead pixel threshold.
- *CPU* - CPU usage of data viewer 
- *Net* - Data rate images are being processed
- *Current FPS* - frame rate since 1 second ago
- *Average FPS* - frame rate since data viewer has started running

User can the "Requested Frame Rate" menu to control rate the viewer processes the images.  User can also use the Statistics "Adjust Limits" window to set additional limits. The window has the following settings

- *Dead Px Threshold* - Dead pixel threshold.  Default to 0xfff0 or 65520.
- *CPU* - Maximum allowed % CPU used.  By default unset
- *Net* - Maximum data rate allowed.  By default unset.


# Scope Application
Scope application displays arbitrary information from a pvAccess channel in a 2D graph. To start:

```bash
c2dv --app scope
```

# Developers Guide

The following information are maintaining and developing C2 Data viewer

## Pip Packaging

To install pip dependencies:
```bash
make pip-dependecies
```

To build a pip package:
```bash
make pip-build
```

To upload the package on PyPI:
```bash
make pip-upload
```

To run the unit tests run:
```bash
make pip-test
```
