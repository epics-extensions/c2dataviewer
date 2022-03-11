# Scope Application
Scope application displays arbitrary information from a pvAccess channel as a time series graph. To start:

```bash
c2dv --app scope --pv <PV>
```

From the application UI, select the fields to plot under "Channels" options.  Click the "Start" checkbox to start plotting.

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
