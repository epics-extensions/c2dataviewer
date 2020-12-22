<p align="center">
  <h1 align="center">C2DataViewer: EPICS7 pvObject Data Viewer</h1>
</p>

C2DataViewer is a Python based data viewer for next generation of APS control system (C2).
It is developed with pyqtgraph, PyQt, and uses pvaPy as pvAccess Python binding.
This is a viewer for pvData structured data objects as transported by pvAccess. Some use cases are a 'scope viewer',
and Area Detector images from the AD pva plugin.

# Quick Start

---
**NOTE**

*c2dv* currently require *pyqtgraph* version `0.10.0`. There is an unresolved issue with the
newer version(s): https://git.aps.anl.gov/C2/conda/data-viewer/-/issues/48.
Correct version of the *pyqtgraph* should be installed manually.

---

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

# Image Application
Image application displays images from an areaDetector pvAccess channel.  To start:
```bash
c2dv --app image --pv <CHANNELNAME>
```
## Image and zoom
This section presents basic information about the displayed image:

- *Size X [px]* - Number of pixels full image has in X direction. If ROI is selected, numbers in parentheses show the range of displayed pixels.
- *Size Y [px]* - Number of pixels full image has in Y direction. If ROI is selected, numbers in parentheses show the range of displayed pixels.
- *Reset zoom* - This button resets  (ROI) to the default settings (Display whole image).

Users can zoom into the image by selecting the region of interest. This can be done by drawing the rectangle around the desired area while the mouse button is pressed.
To restore the full image *Reset zoom* should be pressed.

## Image Adjustment
Image display can be adjusted by setting the black and white points.  "Auto" button automatically adjusts the black and white points to the minimum and maximum values in the image.
Minimum and maximum values of the black and white points can be set throught the Image Levels Adjustment "Adjust limits" window.

## Statistics
Along with the image, the following statistics are displayed:

- *Input type* - image data type
- *Runtime* - total time data viewer has been running
- *Frames* - total number of images viewer has processed
- *Max/Min* - Maximum and minimum values in the image. If ROI is selected, value in the parentheses apply for the selected area.
- *Dead* - Number of pixels that exceed the dead pixel threshold. If ROI is selected, value in the parentheses apply for the selected area.
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

## Triggering
Scope application supports software triggering via external v3 PV. When trigger mode is configured and trigger occur,
selected displayed channels will be updated for the trigger time. Number of samples displayed can be controlled via `Buffer (Samples)` parameter.
Trigger timestamp is always at the middle of the displayed waveform and is marked with the red line.

 Types of the records which can be used as the triggers are:
 - `bi` / `bo` - The trigger event is triggered on transition from `0` -> `1`.
 - `longin` / `longout` - The trigger event is triggered on *any* value change.
 - `calc` - The trigger event is triggered on *any* value change.
 - `event` - The trigger event is triggered on *any* value change.
 - `ai` / `ao` - The trigger event is triggered when the following condition is true: ` PV value >= Trigger Threshold`.

Follow next steps to configure the trigger:

0. Acquisition must be stopped.
1. Enter `Trigger PV` (must be available on the network).
2. Enable `Trigger Mode`.
3. Select `Trigger Threshold` if the input record is of type `ai` or `ao`. For other types this value is ignored.
4. Select desired input channels.
5. Start the acquisition.
6. When the trigger condition is meet, the waveform will draw/update.

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
