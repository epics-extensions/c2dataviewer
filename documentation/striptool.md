# Striptool

Striptool plots channel access and pvAccess scalar variables.

By default striptool plots channel access PVs.  PVs can be specified from command-line, configuration file, or from the GUI.

## Quickstart
```bash
> c2dv --app striptool --pv <comma-separated PV list>
```

## Configuration
PVs can be specified by a configuration file. Below is an example:
```ini
[DEFAULT]
APP=STRIPTOOL

[STRIPTOOL]
SECTION=DISPLAY
DefaultProtocol = ca
Chan1.PV = S:R:reg1
Chan2.PV = S:R:reg2
Chan3.PV = S:R:reg3

[DISPLAY]
Autoscale=true
```
Striptool configurations must start with:

```ini
[DEFAULT]
APP=STRIPTOOL

[SCOPE]
```
Under `SCOPE`, you can optionally add a `SECTION` field to add additional sections, which lists additional sections in the file. Below are configuration settings specific to the scope app for each section.

### ACQUISITION
| Setting | Description
|---|---|
|Buffer| Buffer size |

### DISPLAY
| Setting | Description |
|---|---|
|Refresh| Refresh time in milliseconds |
|Autoscale | Enable autoscale. Can be true or false| 
|Mode| Set display mode.  Valid values are: "normal", "fft", "psd", "diff", "xy"|
|Single\_Axis| Enable single axis. Can be true or false |
|Histogram | Turns on histogram mode. Can be true or false |

### STRIPTOOL
| Setting | Description 
|---|---|
| Section | List of additional sections to read in the config file |
| DefaultProtocol | default PV protocol.  Possible values are 'ca' and 'pva'. Required if protocol is not specified for each PV |
| Chan[ID].PV | PV channel name.  Can specify the protocol by starting name with [proto]://pvname, where [proto] is either 'ca' or 'pva'. Otherwise, use the default protocol. Example: `Chan1.PV = ca://S:R:reg1` |
| Chan[ID].Color | Color to plot for "Chan[ID]". If not set, striptool will set the color. Example: `Chan1.Color = #00FF00` |




