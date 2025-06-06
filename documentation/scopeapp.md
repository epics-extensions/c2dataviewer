# Scope Application
Scope application displays arbitrary information from a pvAccess channel as a time series graph. To start:

```bash
c2dv --app scope --pv=<PV>
```

From the application UI, select the fields to plot under "Channels" options.  Click the "Start" checkbox to start plotting. You can also set fields and connect on startup as follows:

```bash
c2dv --app scope --pv=<PV> --fields=<FIELD1>,<FIELD2>,..  --connect-on-start
```

See `c2dv -h` for all options.

## Zooming
To zoom, scroll using the scroll wheel or trackpad.  To pan, left click and drag.  To see all mouse interactions, see [pyqtgraph's documentation](https://pyqtgraph.readthedocs.io/en/latest/mouse_interaction.html).

You can also configure the X/Y range, by right-click, select options from either the X-axis or Y-axis menus.

## Triggering
Scope application supports software triggering via external v3 PV. When trigger mode is configured and trigger occur,
selected displayed channels will be updated for the trigger time. Number of samples displayed can be controlled via `Buffer` parameter.

Configuring the trigger:

0. Stop acquisition if needed
1. Set PV
2. Set trigger PV. 
3. Set trigger mode to "On Change".
5. Select desired input channels
6. Start the acquisition

When the trigger condition is meet, the waveform will draw/update with the latest data.

If your PV has a time data field, you can sync the plot with the trigger timestamp.  To do this, modify your existing configuration the following way::

0. Stop acquisition if needed
1. If the trigger PV uses `pva` protocol, then set the trigger time field.  If it is `ca` it will automatically use the `timeStamp` field
2. Set data time field for the PV.  This field is used to determine if the trigger PV timestamp falls within the PV waveform
3. Start the acquisition

Trigger timestamp is always at the middle of the displayed waveform and is marked with the red line.



## Configuration
PVs can be specified by a configuration file. 

Example
```ini
[DEFAULT]
APP=SCOPE

[SCOPE]
SECTION=ACQUISITION,CHANNELS

[ACQUISITION]
PV=MyPV:Data
ConnectOnStart=true

[CHANNELS]
Chan1.Field=x
Chan2.Field=y
```
Scope configurations must start with:

```ini
[DEFAULT]
APP=SCOPE

[SCOPE]
SECTION=<SECTION LIST>
```
Where <SECTION_LIST> is a list of the sections in the file. Below are configuration settings specific to the scope app for each section. Note that fields and values are case insensitive.

### SCOPE
| Setting | Description
|---|---|
| Section | List of sections to read in the config file |

### ACQUISITION
| Setting | Description
|---|---|
| PV | EPICS PV name.  By default uses PVAccess protocol.  Can specify protocol by starting name with [proto]://pvname, where [proto] is either 'ca' or 'pva' |
| ConnectOnStart | Attempt to connect to PV on startup. Set to true or false|
| BufferUnit | Units for buffer size.  Can set to 'Samples' or 'Objects'.  If set to Objects, then the buffer size is in terms of number of objects|
|Buffer| Buffer size |

### CHANNELS
| Setting | Description
|---|---|
| Chan[ID].Field | PV field to plot.  Field have scalar array data. Can have up to 4 instances specified  (see example above). Can specify fields inside of nested structures with `struct1.struct2.field1` notation where `struct1`, `struct2` are the structure names, and `field1` is the field name |
| Chan[ID].DcOffset | Extra offset added on top of sample values. Will cause plot Y values to be shifted. |

### DISPLAY
| Setting | Description |
|---|---|
|Refresh| Refresh time in milliseconds |
|Autoscale | Enable autoscale. Set to true or false| 
|Mode| Set display mode.  Valid values are: "normal", "fft", "psd", "diff", "autocorrelate_fft"|
|Single\_Axis| Enable single axis. Set to true or false |
|Histogram | Turns on histogram mode. Set to true or false |

### CONFIG
| Setting | Description |
|---|---|
|XAxes| PV field to use for X-axis values in X vs Y mode|
|MajorTicks| Sample interval length for major ticks|
|MinorTicks| Sample interval length for minor ticks|

## TRIGGER
| Setting | Description |
|---|---|
|Trigger| Trigger PV |
|Trigger_Mode | Trigger mode. Can be "Off", "OnChange", "GtThreshold", or "LtThreshold" |
