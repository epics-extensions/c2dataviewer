# Image Application
Image application displays images from an areaDetector pvAccess channel.  To start:
```bash
c2dv --app image --pv <CHANNELNAME>
```
## Image Zoom
Users can zoom into the image by selecting the region of interest. This can be done by drawing the rectangle around the desired area while the mouse button is pressed.
Users can also scroll there mouse wheel, if that is available, or use a two-finger up/down movement on their touchpad to zoom in/out incrementally at the mouse position by a specified zoom factor. By default the zoom factor is set to 5%.
To restore the full image *Reset zoom* should be pressed from the control panel or the user can right click while the cursor is on the image window and select *Reset zoom* from the menu there as well.

## Image Panning
Once a user has zoomed in on a section of the image, they can pan the zoom window to diplay different sections of the image within those zoom parameters by dragging their mouse while holding down the right button (or holding down 2 fingers for laptops without a right button).

## ROI Mode
The ROI mode allows user to select a ROI rectangle, which stays displayed
on top of the image, along with the mid-lines drawn from the rectangle
towards the image rules (if those are displayed). To enable the ROI mode
right click on the image window and select the *Enable ROI Mode* from the
menu.

## Control Panel
Users can hide and restore control panel by right-clicking on the image panel.

## Display Coordinates and Intensity
Users can enable a mouse dialog to display the pixel coordinates and respective intesities by first right-clicking their mouse while it is over the image window and then selecting the *Show Coordinates and Intensity* option from the menu. Similarly, to disable this mouse dialog when it is being displayed, users can first right-click their mouse while it is over the image window and then select the *Hide Coordinates and Intensity* option from the menu.

## Compressed Images
At the moment the following compression algorithms are supported:
- blosc (requires 'blosc' module)
- bslz4 (requires 'bitshuffle' module)
- lz4 (requires 'lz4' module)

## Settings
Users can adjust a number of parameters and resource limits by clicking on the *Settings* button in the control panel.

