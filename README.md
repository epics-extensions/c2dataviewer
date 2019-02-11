
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
conda build . -c epics
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

# TODO
* Remove hard code EPICS7 PV field names [Done]

Currently there are some hard coded field names, which are inherited from old code, for example "ArrayId".

* User selectable/configurable EPICS field name [Done]

Provide a mechanism to allow user to configure X axes. If it is not provided, it will use data count for the plotting.

It could be from command line, or selectable from drop down menu.

* Use time diff as X axes [Done]
    * Allow user to select time axis

* Image initial resize and auto gain control [Done]

* Separate UI from data source for image [Done]

* Bug fix when changing frame rate and/or camera [Done]

* Plot against multiple vertical axes
    * Discussed, and decided to gather more requirements first before coding.

* Show statistics data for Scope [Done]

* Add histogram support [Done]

* Add Binning support [Done]

* Support different plotting 
    * FFT [Done]
    * PSD [Done]
    * Diff [Done]
    * X vs Y

* Filtering function [Done]

Filter out data which is out of user specified range (max & min)

* Keep latest plot when stopping plotting [Done]

* BUG: buffer size from configuration is not initialized properly. [Done]

* ENH: Improve model handling: merge pvAccess layer for different application into one class. [Done]

* ENH: Handling channel connection time out in a more proper way instead of crashing [Done]

* ENH: Handling empty image channel with no data inside in a more proper way instead of crashing [Done] 

* Add trigger support

* Handle PV disconnection in a more proper way

When a PV disconnected in the middle, data source (scope_data.py) throws out a RuntimeError, which is proper.
Currently the UI does not catch that exception, which causes the UI crash.
This behavior shall be improved to make the application more robust.
A popup window shall be used instead of crashing the application. 

* Bug to fix updating rate drop caused by CPU spark during resizing for image

* Unit test suite

* CI testing integration

* Logging for error and warning message
