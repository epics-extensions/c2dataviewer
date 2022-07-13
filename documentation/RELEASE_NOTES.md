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

