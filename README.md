
<p align="center">
  <h1 align="center">C2DataViewer: EPICS7 pvObject Data Viewer</h1>
</p>

C2DataViewer is a Python based data viewer for next generation of APS control system (C2).
It is developed with pyqtgraph, PyQt, and uses pvaPy as pvAccess Python binding.
This is a viewer for pvData structured data objects as transported by pvAccess. Some use cases are a 'scope viewer',
and Area Detector images from the AD pva plugin.



# TODO
* Remove hard code EPICS7 PV field names

Currently there are some hard coded field names, which are inherited from old code, for example "ArrayId".

* User selectable/configurable EPICS field name

Provide a mechanism to allow user to configure X axes. If it is not provided, it will use data count for the plotting.

It would be from command line, or selectable from drop down menu.

* Use time diff as X axes
    * Allow user to select time axes

* Show statistics data

* Add histogram support

* Add Binning support

* Support different plotting
    * FFT
    * PSD
    * Diff
    * X vs Y
* Plot against multiple axes

* Add trigger support

* Unit test suite

* Logging for error and warning message
