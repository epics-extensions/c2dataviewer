# Striptool

Striptool plots channel access and pvAccess scalar variables.

By default striptool plots channel access PVs.  PVs can be specified from command-line, configuration file, or from the GUI.

## Quickstart
```bash
> c2dv --app striptool --pv <comma-separated PV list>
```

## Configuration
PVs can be specified by a configuration file. Below is an example:
```
[DEFAULT]
APP=STRIPTOOL

[STRIPTOOL]
DefaultProtocol = ca
Chan1.PV = S:R:reg1
Chan2.PV = S:R:reg2
Chan3.PV = S:R:reg3
```

Below are settings specific to striptool
| Setting | Description 
|---|---|
| DefaultProtocol | default PV protocol.  Possible values are 'ca' and 'pva'. Required if protocol is not specified for each PV |
| Chan[ID].PV | PV channel name.  Can specify the protocol by starting name with [proto]://pvname, where [proto] is either 'ca' or 'pva'. Otherwise, use the default protocol. Example: `Chan1.PV = ca://S:R:reg1` |
| Chan[ID].Color | Color to plot for "Chan[ID]". If not set, striptool will set the color. Example: `Chan1.Color = #00FF00` |

Go [here](configsettings.md) for more configuration settings


