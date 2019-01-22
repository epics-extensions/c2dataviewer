
<p align="center">
  <h1 align="center">C2DataViewer: EPICS7 pvObject Data Viewer</h1>
</p>

C2DataViewer is a Python based data viewer for next generation of APS control system (C2).
It is developed with pyqtgraph, PyQt, and uses pvaPy as pvAccess Python binding.
This is a viewer for pvData structured data objects as transported by pvAccess. Some use cases are a 'scope viewer',
and Area Detector images from the AD pva plugin.



# TODO
* Remove hard code EPICS7 PV field names [Done]

Currently there are some hard coded field names, which are inherited from old code, for example "ArrayId".

* User selectable/configurable EPICS field name [Done]

Provide a mechanism to allow user to configure X axes. If it is not provided, it will use data count for the plotting.

It could be from command line, or selectable from drop down menu.

* Use time diff as X axes [Done]
    * Allow user to select time axis

* Image initial resize and auto gain control [Done]

* Separate UI from data source for image

* Bug to fix updating rate drop caused by CPU spark during resizing for image

* Plot against multiple vertical axes

* Show statistics data

* Add histogram support

* Add Binning support

* Support different plotting
    * FFT
    * PSD
    * Diff
    * X vs Y

* Filtering function

Filter out data which is out of user specified range (max & min)

* Add trigger support

* Handle PV disconnection in a more proper way

When a PV disconnected in the middle, data source (scope_data.py) throws out a RuntimeError, which is proper.
Currently the UI does not catch that exception, which causes the UI crash.
This behavior shall be improved to make the application more robust.
A popup window shall be used instead of crashing the application. 

* Unit test suite

* CI testing integration

* Logging for error and warning message
