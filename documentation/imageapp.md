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

## Compressed Images
At the moment the following compression algorithms are supported:
- blosc (requires 'blosc' module)
