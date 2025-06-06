# Release 1.14.8 (05/06/2025)
- Remove python 3.7 build
- fix failure with x-axis set and trigger is not set
- fix diff mode and removed unimplemented xy mode
- added new autocorrelation FFT mode

# Release 1.4.7 (03/03/2025)
- add python 3.7 and 3.11 to conda build config

# Release 1.14.6 (03/03/2025)
- Add support to trigger without timestamp data
- fixed PV trigger configuration
- Shutdown plot when scope app or striptool app exits
- Expand user in configuration path

# Release 1.14.5 (02/27/2025)
- replace use of deprecated ParameterTree field

# Release 1.14.4 (02/26/2025)
- Fixed missing buffer unit error that started occurring when upgraded python libraries

# Release 1.14.2 (01/30/2025)
- force conda build to python 3.10

# Release 1.14.1 (12/18/2024) 
-Put restriction that pyqtgraph must be at least 0.12, to avoid invalid Qt call errors for older pyqt versions

# Release 1.14.0 (12/18/2024)
- Fix striptool and scope app documentation
- Made c2dv compatible with pyqtgraph 0.13 and removed pyqtgraph version restriction

# Release 1.13.2 (05/22/2024)
- fix single axis, histogram, and display mode configuration
- update striptool and scope app config documentation to reflect what is supported

# Release 1.13.1 (05/10/2024)
- Fixed scope mouse over behavior so you can pan like before

# Release 1.13.0 (04/22/2024)
- Add ability to set server queue size for image viewer, which can reduce
  number of dropped frames at higher image rates
- Add ability to display moving average images

# Release 1.12.4
- Fix payload start for LZ4 and BSLZ4 compression codecs

# Release 1.12.3
- Fix buffer size configuration bug

# Release 1.12.2
- Fix startup error for scope application

# Release 1.12.1 (04/12/2024)

- Add ability to display image rulers
- Add roi-mode (permanent rectangle on top of image)
- Fix statistics calculation for the case when requested rate is faster
  than IOC rate
- Fix performance issue caused by profile calculation even when profiles
  are not displayed
- Update mouseover textbox when plot updates
- Insert new PV channel data from most current time in striptool

# Release 1.12.0 (04/08/2024)

- Make compression dependencies optional for pip package
  and remove them from conda packages
- scope app: add support to view field values on mouse over 

# Release 1.11.4 (04/08/2024)
- scope app: Fixed bug configuring fields at startup

# Release 1.11.3 (01/24/2024)

- Add support for lz4 and bitshuffle/lz4 codecs

# Release 1.11.2 (08/08/2023)
- Fixed unit test

# Release 1.11.1 (08/08/2023)
- Show ROI size in control panel

# Release 1.11.0 (08/07/2023)

- Added support for displaying x,y, intensity from mouse position
- Added support for zooming and resetting zoom via mouse
- Bug fixes in image app

# Release 1.10.2 (07/14/2023)
- Fix image profile type error

# Release 1.10.1 (07/13/2023)

- Fixed bugs in striptool, scope, and image app
- Support starting image app without a PV

# Release 1.10.0 (04/07/2023)
- Upgrade to pyqtgraph 0.12.4
- Add license information to source- 

# Release 1.9.1 (03/23/2023)

- Fixed pip build

# Release 1.9.0 (03/23/2023)

- Add ability to hide control panel via right-click on the image panel
- Add support for displaying compressed images (blosc compression)

# Release 1.8.6 (02/22/2023)

- Add new configuration options

# Release 1.8.5 (02/07/2023)

- Fixed flaky tests and remove python version dependency

# Release 1.8.4 (08/05/2022)

- Fixed unit test failure

# Release 1.8.3 (08/03/2022)

- Add new configuration options

# Release 1.8.2 (07/22/2022)
## Scope app
- Add ability to set fields and connect on startup via command-line options and config

# Release 1.8.1 (07/19/2022)

- Fix config error

# Release 1.8.0 (07/19/2022)
- Add major/minor ticks to scope app
- Fix scope app so user can manually set x/y range

# Release 1.7.7 (07/13/2022)
- Fixed buffer size auto adjustment

# Release 1.7.6 (05/19/2022)
## Scope app
- Add ability to change buffer size by number of objects instead of number of samples
- Fix auto adjust buffer size to set to average object size

# Release 1.7.5 (05/11/2022)
- Add environment variable for turning on logging

## Scope app
- Load field list if failed PV comes up 

## Image app
- Add more debug information to error message if failed to read PV data

# Release 1.7.4 (05/04/2022)
## Scope app
- Fixed several bugs in trigger support and improved usability
- Added ability to autoscale buffer to fit trigger
- Added ability to pass in CA waveform into scope app


# Release 1.7.3 (04/26/2022)
## Image app
- make color mode optional

# RELEASE 1.7.2
- bug fixes

# RELEASE 1.7.1
- bug fixes

# RELEASE 1.7.0
## New Features
- Added new striptool application. 
- Scope app: default buffer size to initial waveform size
- bug fixes

# RELEASE 1.6.0
## New Features
- Add 20 and 30Hz options to image app
- Don't exit application if PV is invalid
- Add ability to switch to different PVs to image app
- Show PV connection status in scope and image app

# RELEASE 1.5.2
## Bug fixes
- Prevent zoom if click outside of image
- Hide non-numeric array fields in scope app
- Fixed screen freeze when image profiles are on
# RELEASE 1.5.1
- Bug fixes

# RELEASE 1.5.0
## Image App
New Features
- Add ability to graph the horizontal and vertical image profiles of the image
- Add support for RGB1, RGB2, and RGB3 color formats
- Add statistics for received data, average/current received data rate, missed frames, and average/current missed frames per second
- Add configuration for the image statistics to ignore a certain length of pixels at the beginning of the image.  This is off by default
- Turn off counting "dead pixels" by default
- Add button for resetting statistics
- Moved all configuration for limits and other settings in a single "Settings" window.


# RELEASE 1.4.0
## Scope App
New Features
- Ability to apply Hamming window to FFT
- Ability to plot moving average
- Ability to plot multiple channels with multiple Y axis's
- Ability to trigger plot on CA PV change. See README for documentation.

## Image App
New Features
- Ability to zoom image using mouse or touchpad.  See README for documentation.
- Ability to freeze image

# RELEASE 1.3.0
**New features**
- All integer (unsigned/signed, 8, 16, 32, 64 bit) and floating point (float, double) data types are supported in Image viewer
- Black and white values can be set via text box or slider
- Pip packaging support

**Bug fixes**
- Image Viewer no longer freezes if image data type changes

# RELEASE 1.2.5
- fixed window resize bug
- sync package version with Git tag

