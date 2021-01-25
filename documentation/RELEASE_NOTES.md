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

