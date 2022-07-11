# Scope Application
Scope application displays arbitrary information from a pvAccess channel as a time series graph. To start:

```bash
c2dv --app scope --pv <PV>
```

From the application UI, select the fields to plot under "Channels" options.  Click the "Start" checkbox to start plotting.

## Mouse interactions
To zoom, scroll using the scroll wheel or trackpad.  To pan, left click and drag.  To see all mouse interactions, see [pyqtgraph's documentation](https://pyqtgraph.readthedocs.io/en/latest/mouse_interaction.html).

## Triggering
Scope application supports software triggering via external v3 PV. When trigger mode is configured and trigger occur,
selected displayed channels will be updated for the trigger time. Number of samples displayed can be controlled via `Buffer` parameter.
Trigger timestamp is always at the middle of the displayed waveform and is marked with the red line.

Configuring the trigger:

0. Stop acquisition if needed
1. Set PV
2. Set trigger PV. If the trigger PV uses `pva` protocol, then set the trigger time field.
3. Set trigger mode to "On Change".
4. Set data time field for the PV.  This field is used to determine if the trigger PV timestamp falls within the PV waveform
5. Select desired input channels
6. Start the acquisition

When the trigger condition is meet, the waveform will draw/update.
