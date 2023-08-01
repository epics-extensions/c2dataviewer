# Image Application
Image application displays images from an areaDetector pvAccess channel.  To start:
```bash
c2dv --app image --pv <CHANNELNAME>
```
## Image Zoom
Users can zoom into the image by selecting the region of interest. This can be done by drawing the rectangle around the desired area while the mouse button is pressed.
To restore the full image *Reset zoom* should be pressed.

## Control Panel
Users can hide and restore control panel by right-clicking on the image panel.

# Display Coordinates and Intensity
Users can enable a mouse dialog to display the pixel coordinates and respective intesities by first right-clicking their mouse while it is over the image window and then selecting the *Show Coordinates and Intensity* option from the menu. Similarly, to disable this mouse dialog when it is being displayed, users can first right-click their mouse while it is over the image window and then select the *Hide Coordinates and Intensity* option from the menu.

## Compressed Images
At the moment the following compression algorithms are supported:
- blosc (requires 'blosc' module)
