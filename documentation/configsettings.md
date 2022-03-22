# Generic Configuration Settings
Configuration common for all c2dataviewer applications.  Default configuration for c2dataviewer is defined [here](../c2dataviewer/c2dv.cfg).

## Sections

### DEFAULT
| Setting | Description |
|---|---|
|APP| set default application.  Possible values are `IMAGE`, `SCOPE`, and `STRIPTOOL`

### ACQUISITION
| Setting | Description |
|---|---|
|BUFFER| Buffer size |
|TRIGGER| Trigger PV name and protocol, which comes with format of `proto://pv_name`. `proto` can either be `pva` or `ca`  |
|WAIT_TRIGGER| Turns on/off trigger mode. Possible values are `TRUE`, `FALSE` |

### DISPLAY
| Setting | Description |
|---|---|
|FFT_FILTER| FFT filter type. Possible values are `NONE`, `HAMMING` |
|AVERAGE| Size for moving average. |
|AUTOSCALE| Turns on/off autoscale. Possible values are `TRUE`, `FALSE` |
|SINGLE_AXIS| Turns on/off single axis.  Possible values are `TRUE`, `FALSE`|
|HISTOGRAM| Turns on/off histogram.  Possible values are `TRUE`, `FALSE`|
|N_BIN| Number of bins |
|REFRESH| Refresh time in milliseconds |
