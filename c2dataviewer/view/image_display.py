# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities for image display

@author: Guobao Shen <gshen@anl.gov>
"""
import numpy as np
from pyqtgraph import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.widgets.RawImageWidget import RawImageWidget
from pvaccess import PvaException

from .image_definitions import *
from .image_profile_display import ImageProfileWidget

class ImagePlotWidget(RawImageWidget):

    ZOOM_LENGTH_MIN = 4 # Using zoom this is the smallest number of pixels to display in each direction

    _set_image_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None, **kargs):
        RawImageWidget.__init__(self, parent=parent, scaled=True)

        self._set_image_signal.connect(self._set_image_signal_callback)
        self._image_mutex = QtCore.QMutex()

        self._noagc = kargs.get("noAGC", False)
        # self.camera_changed()
        self._agc = False
        self._lastTimestamp = None
        self._freeze = False

        self.__last_array_id = None
        self.dataType = None
        self.MB_received = 0.0
        self.frames_displayed = 0
        self.frames_missed = 0

        # Image properties
        self.dimensions = None
        self.color_mode = None
        self.x = None
        self.y = None
        self.z = None
        self.fps = -1

        # max value of image pixel
        self.maxVal = 0
        self.minVal = 0
        self.mutex = QtCore.QMutex()

        self._white = 255.0
        self._black = 0.0

        # Image profiles
        self.image_profile_widget = None

        # Last displayed image
        self.last_displayed_image = None

        # Widget properties
        self.image_width_pixels = 0
        self.image_height_pixels = 0

        # Zoom parameters
        self.__zoomSelectionIndicator = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)
        self.__zoomDict = {
            "isZoom": False,
            'xoffset': 0,
            'yoffset': 0,
            'width': 0,
            'height': 0,
        }

        # ROI
        self.roi_origin = None

        # Limit control to avoid overflow network for best performance
        self._pref = {"Max": 0,
                      "Min": 0,
                      "DPX": 0,
                      "DPXEnabled": False,
                      "DPXLimit": 0x00,
                      "EmbeddedDataLen" : 0,
                      "CPU": 0,
                      "EnableCPULimit": False,
                      "CPULimit": 50,
                      "Net": 0,
                      "EnableNetLimit": False,
                      "NetLimit": 100,
                      "FPS": 0,
                      "FPSLimit": None}

        self._isInputValid = False
        self._inputType = ""
        self.dead_pixels = [0]
        self._max = [0]
        self._min = [0]
        self.dead_pixels_roi = [0]
        self._maxRoi = [0]
        self._minRoi = [0]

        self._scaling = 1.0
        self._agc = True
        self._lastTimestamp = None

        # Imagecontroller callbacks
        self.updateGuiBlackLimits = None
        self.updateGuiWhiteLimits = None
        self.getGuiBlackLimits = None
        self.getGuiWhiteLimits = None
        self.updateGuiBlack = None
        self.updateGuiWhite = None

        self.datasource = None
        self.data = None

        self.dataTypesDict = {
            'byteValue' :   {'minVal' : int(-2**8 / 2),   'maxVal' : int(2**8 / 2 - 1),  'npdt' : "int8",   },
            'ubyteValue' :  {'minVal' : 0           ,     'maxVal' : int(2**8 - 1),      'npdt' : "uint8",  },
            'shortValue' :  {'minVal' : int(-2**16 / 2),  'maxVal' : int(2**16 / 2 - 1), 'npdt' : "int16",  },
            'ushortValue' : {'minVal' : 0               , 'maxVal' : int(2**16 - 1),     'npdt' : "uint16", },
            'intValue' :    {'minVal' : int(-2**32 / 2),  'maxVal' : int(2**32 / 2 - 1), 'npdt' : "int32",  },
            'uintValue' :   {'minVal' : 0               , 'maxVal' : int(2**32 - 1),     'npdt' : "uint32", },
            'longValue' :   {'minVal' : int(-2**64 / 2),  'maxVal' : int(2**64 / 2 - 1), 'npdt' : "int64",  },
            'ulongValue' :  {'minVal' : 0               , 'maxVal' : int(2**64 - 1),     'npdt' : "uint64", },
            'floatValue' :  {'minVal' : int(-2**24),      'maxVal' : int(2**24),         'npdt' : "float32",},
            'doubleValue' : {'minVal' : int(-2**53),      'maxVal' : int(2**53),         'npdt' : "float64",},
        }

        # Acquisition timer used to get specific request frame rate
        self.acquisition_timer = QtCore.QTimer()

    def resizeEvent(self, event):
        """
        This method is called by the Qt when the widget change size. We use this to recalculate the
        size of the image od the display.

        :param event: (QResizeEvent) Object holding information about the event.
        :return:
        """
        self.calc_img_size_on_screen()

    def mousePressEvent(self, event):
        """
        This method is event handler for the mouse click event and is called by the Qt framework.

        :param event: (QMouseEvent) Parameter holding event details.
        :return: (None)
        """
        # Get location of the click
        click_position = event.pos()
        x_position = click_position.x()
        y_position = click_position.y()

        # Check if the press happened on the image
        img_width, img_height = self.calc_img_size_on_screen()
        if (x_position > img_width or y_position > img_height):
            return

        # Mouse buttom was pressed on the image. We start panning.
        self.roi_origin = click_position
        self.__zoomSelectionIndicator.setGeometry(QtCore.QRect(self.roi_origin, QtCore.QSize()))
        self.__zoomSelectionIndicator.show()

    def mouseMoveEvent(self, event):
        """
        This method is event handler for the mouse move event and is called by the Qt framework.

        :param event: (QMouseEvent) Parameter holding event details.
        :return: (None)
        """
        if self.roi_origin is None:
            return

        # Mouse is moving, while selecting roi. Redraw the selection rectangle.
        self.__zoomSelectionIndicator.setGeometry(
            QtCore.QRect(self.roi_origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        """
        This method is event handler for the mouse button release event and is called by the Qt framework.

        :param event: (QMouseEvent) Parameter holding event details.
        :return: (None)
        """
        if self.roi_origin is None:
            return

        # We made the roi selection
        # Hide selection rectangle
        self.__zoomSelectionIndicator.hide()

        # Get information about the widget dimensions
        panEnd = QtCore.QPoint(event.pos())
        imageGeometry = self.geometry().getRect()
        widget_width = imageGeometry[2]
        widget_hight = imageGeometry[3]

        # Calculate x parameters, x min/max and size in pixels
        xmin = self.roi_origin.x()
        xmax = panEnd.x()
        if xmin > xmax:
            xmax, xmin = xmin, xmax
        if xmin < 0:
            xmin = 0
        if xmax > widget_width:
            xmax = widget_width

        # Calculate y parameters, y min/max and size in pixels
        ymin = self.roi_origin.y()
        ymax = panEnd.y()
        if ymin > ymax:
            ymax, ymin = ymin, ymax
        if ymin < 0:
            ymin = 0
        if ymax > widget_hight:
            ymax = widget_hight

        self.roi_origin = None

        # Calculate zoomed image parameters
        self.__calculateZoomParameters(xmin, xmax, ymin, ymax)

    def __calculateZoomParameters(self, xminMouse, xmaxMouse, yminMouse, ymaxMouse):
        """
        This method calculate pixel offsets and sizes of the image to get zoomed image on the selected ROI.

        :param xminMouse: (Int) Min X coordinate of the selection in the display pixels. Relative to the widget.
        :param xmaxMouse: (Int) Max X coordinate of the selection in the display pixels. Relative to the widget.
        :param yminMouse: (Int) Min Y coordinate of the selection in the display pixels. Relative to the widget.
        :param ymaxMouse: (Int) Max Y coordinate of the selection in the display pixels. Relative to the widget.
        :return: (None)
        """
        # Widget sizes
        wWidth = self.width()
        wHeight = self.height()

        # Current zoom parameters
        xOffset, yOffset, width, height = self.get_zoom_region()

        # Get pixel size
        pixelSize = min (
            wWidth / width,
            wHeight / height
        )

        # Calculate new x direction zoom parameters
        xOffset += int(xminMouse / pixelSize)
        width = int((xmaxMouse - xminMouse) / pixelSize)

        # Calculate new y direction zoom parameters
        yOffset += int(yminMouse / pixelSize)
        height = int((ymaxMouse - yminMouse) / pixelSize)

        # Write to dict
        self.set_zoom_region(xOffset, yOffset, width, height)

    def setup_profiles(self, grid_layout):
        """
        Build image_profile_widget with the specified grid layout.

        :param grid_layout: (QGridLayout) Reference to the grid layout where image
                                            widget is and the profiles should be added.
        :return: None
        """
        self.image_profile_widget = ImageProfileWidget(grid_layout)

    def set_zoom_region(self, xOffset, yOffset, width, height):
        """
        Set zoom region. If values are out of range, values will be clipped.

        :param xOffset: (int) Offset in X direction from start of the image in image pixels.
        :param yOffset: (int) Offset in Y direction from start of the image in image pixels.
        :param width: (int) Width of the image in image pixels to display.
        :param height: (int) Height of the image in image pixels to display.
        """
        if width < self.ZOOM_LENGTH_MIN:
            width = self.ZOOM_LENGTH_MIN
        if height < self.ZOOM_LENGTH_MIN:
            height = self.ZOOM_LENGTH_MIN

        if xOffset < self.x - self.ZOOM_LENGTH_MIN:
            self.__zoomDict['xoffset'] = xOffset
        else:
            self.__zoomDict['xoffset'] = self.x - self.ZOOM_LENGTH_MIN

        if yOffset < self.y - self.ZOOM_LENGTH_MIN:
            self.__zoomDict['yoffset'] = yOffset
        else:
            self.__zoomDict['yoffset'] = self.y - self.ZOOM_LENGTH_MIN

        if self.__zoomDict['xoffset'] + width <= self.x:
            self.__zoomDict['width'] = width
        else:
            self.__zoomDict['width'] = self.x - self.__zoomDict['xoffset']

        if self.__zoomDict['yoffset'] + height <= self.y:
            self.__zoomDict['height'] = height
        else:
            self.__zoomDict['height'] = self.y - self.__zoomDict['yoffset']

        self.__zoomDict['isZoom'] = True

        if self.data:
            self.display(self.data, zoomUpdate=True)

    def set_freeze(self, flag):
        """
        Freeze or unfreeze the image.

        :parama flag: (bool) True to freeze the image, False otherwise.
        :return:
        """
        self._freeze = flag
        if self.datasource is not None:
            if self._freeze:
                self.stop()
            else:
                self.start()

    def reset_zoom(self):
        """
        This method will reset __zoomDict to the default values (no zoom).

        :return: (None)
        """
        self.__zoomDict['isZoom'] = False
        self.__zoomDict['xoffset'] = 0
        self.__zoomDict['yoffset'] = 0
        self.__zoomDict['width'] = self.x
        self.__zoomDict['height'] = self.y

        if self.data:
            self.display(self.data, zoomUpdate=True)

    def is_zoomed(self):
        """
        Check if displayed image is zoomed.

        :return: (bool) True if image is zoomed, False otherwise.
        """
        return self.__zoomDict['isZoom']

    def get_zoom_region(self):
        """
        Get displayed region in image pixels.

        :return: (None or tuple)
        """
        return (
                self.__zoomDict['xoffset'],
                self.__zoomDict['yoffset'],
                self.__zoomDict['width'],
                self.__zoomDict['height'],
                )

    def calc_img_size_on_screen(self):
        """
        Calculate how big is the image on the display in pixels.

        :return: (int, int) Image width and height in pixels.
        """
        # Widget sizes
        window_width = self.width()
        window_height = self.height()

        # Current zoom parameters
        _, _, width, height = self.get_zoom_region()

        if width == 0 or height == 0:
            return

        # Get pixel size
        pixel_size = min (
            window_width / width,
            window_height / height
        )

        image_width = pixel_size * width
        image_height = pixel_size * height

        return image_width, image_height

    def wait(self):
        """

        :return:
        """
        self.mutex.lock()

    def signal(self):
        """

        :return:
        """
        self.mutex.unlock()

    def set_datasource(self, source):
        """
        Set data source, and start data taking

        :param source:
        :return:
        """
        if source is not None:
            self.datasource = source
            # self.__update_dimension(self.datasource.get())
            self.acquisition_timer.timeout.connect(self.get)

    def __update_dimension(self, data):
        """

        :param data:
        :return:
        """

        # Get color mode
        attributes = data['attribute']
        if any(('name' in attr and attr['name'] == "ColorMode") for attr in attributes ):
            for attribute in attributes:
                if attribute['name'] == "ColorMode":
                    self.color_mode = attribute['value'][0]['value']
        else:
            raise RuntimeError(f"NDArray does not contain ColorMode Attribute.")

        # Get dimensions
        dims = data['dimension']
        self.dimensions = len(dims)

        if self.dimensions == 2 and self.color_mode == COLOR_MODE_MONO:
            x = dims[0]
            y = dims[1]
            z = None
        elif self.dimensions == 3 and self.color_mode == COLOR_MODE_RGB1:
            x = dims[1]
            y = dims[2]
            z = dims[0]
        elif self.dimensions == 3 and self.color_mode == COLOR_MODE_RGB2:
            x = dims[0]
            y = dims[2]
            z = dims[1]
        elif self.dimensions == 3 and self.color_mode == COLOR_MODE_RGB3:
            x = dims[0]
            y = dims[1]
            z = dims[2]
        else:
            raise RuntimeError(f"Invalid data/color mode data.")

        if (x['size'] != self.x) or (y['size'] != self.y) or (z is not None and z['size'] != self.z):
            self.x = x['size']
            self.y = y['size']
            self.z = z['size'] if z is not None else None
            self.reset_zoom()

    def set_black(self, value):
        """

        :param value:
        :return:
        """
        self._black = value

    def get_black(self):
        """

        :param value:
        :return:
        """
        return self._black

    def set_white(self, value):
        """

        :param value:
        :return:
        """
        self._white = value

    def get_white(self):
        """

        :param value:
        :return:
        """
        return self._white

    def start(self):
        """

        :return:
        """
        if not self._freeze:
            if self.fps == -1:
                self.datasource.start(routine=self.monitor_callback)
            else:
                self.acquisition_timer.start(1000/self.fps)

    def stop(self):
        """

        :return:
        """
        self.acquisition_timer.stop()
        try:
            if self.datasource is not None:
                self.datasource.stop()
        except RuntimeError as e:
            print(repr(e))

    def set_framerate(self, value):
        """

        :param value:
        :return:
        """
        self.wait()
        self.stop()
        self.fps = value
        self.start()
        self.signal()

    def monitor_callback(self, data):
        """

        :param data:
        :return:
        """
        self.data = data
        self.wait()
        try:
            self.display(self.data)
            self.signal()
        except RuntimeError:
            self.signal()

    def get(self):
        """

        :return:
        """
        try:
            self.data = self.datasource.get('field()')
        except PvaException:
            self.stop()
            # raise e

        self.wait()
        try:
            self.display(self.data)
            self.signal()
        except RuntimeError:
            self.signal()

    def camera_changed(self, value):
        """

        :return:
        :raise RuntimeError:
        """
        self.wait()
        self._agc = False
        self._lastTimestamp = None
        try:
            self.datasource.update_device(value)
        except PvaException as e:
            # TODO wrap PvaException from pvaPy in a better way for other interface
            # pvAccess connection error
            # release mutex lock
            self.signal()
            # stop display
            self.stop()
            # Raise runtime exception
            raise RuntimeError(str(e))
        try:
            # self.__update_dimension(self.datasource.get())
            pass
        except ValueError as e:
            self.stop()
            self.signal()
            raise e

        try:
            self.set_scaling()
            self.start()
            self.signal()
        except ValueError as e:
            self.stop()
            self.signal()
            raise e

    def get_preferences(self):
        """
        :return: (dict) Preferences dictionary.
        """
        return self._pref

    def set_preferences(self, preferences):
        """
        Set preferences.

        :param preferences: (dist) Preference dict.
        """
        self._pref.update(preferences)

    def enable_auto_white(self):
        """
        Enable auto white calibration for image

        :return:
        """
        self._agc = True

    def set_BlackLimitsCallback(self, function):
        """

        :return:
        """
        self.updateGuiBlackLimits = function

    def set_WhiteLimitsCallback(self, function):
        """

        :return:
        """
        self.updateGuiWhiteLimits = function

    def set_getBlackWhiteLimits(self, getBlackLimitsFunction, getWhiteLimitsFunction):
        """

        :return:
        """
        self.getGuiBlackLimits = getBlackLimitsFunction
        self.getGuiWhiteLimits = getWhiteLimitsFunction

    def set_BlackCallback(self, function):
        """

        :return:
        """
        self.updateGuiBlack = function

    def set_WhiteCallback(self, function):
        """

        :return:
        """
        self.updateGuiWhite = function

    def set_scaling(self, scale=None):
        """

        :param scale:
        :return:
        """
        if scale is None:
            if self.x is None:
                self._scaling = 1.0
            else:
                self._scaling = self.width()/self.x
        else:
            self._scaling = scale

    def display(self, data, zoomUpdate = False):
        """
        Display and update image using passed data.

        :param data: Channel PV data.
        :param zoomUpdate: (bool) Must be False to display new image. True if method
                            is called to update the current displayed image with new
                            zoom.
        :return:
        """
        # Update dimensions
        if not zoomUpdate:
            self.__update_dimension(data)

        # Determinate input data type
        data_types = data['value'][0].keys()
        assert len(list(data_types)) == 1
        inputType = list(data_types)[0]

        # Check if the input is valid
        if not inputType in self.dataTypesDict or not self.color_mode in COLOR_MODES:
            self._isInputValid = False
            raise RuntimeError('No recognized image data received.')
        else:
            self._isInputValid = True

        # Lookup required infomartion for the current input type
        imgArray = data['value'][0][inputType]
        sz = imgArray.nbytes
        maxVal = self.dataTypesDict[inputType]['maxVal']
        minVal = self.dataTypesDict[inputType]['minVal']
        npdt = self.dataTypesDict[inputType]['npdt']
        embeddedDataLen = self._pref['EmbeddedDataLen']

        # Configure GUI for the correct type
        if inputType != self._inputType:
            self.configureGuiLimits(inputType)

        self._inputType = inputType

        # Handle timestamp
        ts = data['timeStamp']
        if ts == self._lastTimestamp and not zoomUpdate:
            # if timstamp hasn't changed, its not a new image
            return
        self._lastTimestamp = ts

        # Update numbers of MBytes received (bytes => kBytes => MBytes conversion)
        if not zoomUpdate:
            self.MB_received += sz/1000.0/1000.0

        # Get image statistics
        if maxVal != self.maxVal:
            self.maxVal = maxVal
        if minVal != self.minVal:
            self.minVal = minVal

        # Resize to get a 2D array from 1D data structure
        if self.x == 0 or self.y == 0 or self.color_mode is None:
            # return
            raise RuntimeError("Image dimension not initialized")
        img = transcode_image(imgArray, self.color_mode, self.x, self.y, self.z)

        # Count dead pixels
        if self._pref['DPXEnabled']:
            current_img_dead_pixels = (imgArray[embeddedDataLen:] > self._pref["DPXLimit"]).sum()
        else:
            current_img_dead_pixels = 0
        self.dead_pixels.append(current_img_dead_pixels)
        self.dead_pixels = self.dead_pixels[-3:]

        # Record max/min pixel values on ROI
        if img.ndim == 2:
            self._max = imgArray[embeddedDataLen:].max()
            self._min = imgArray[embeddedDataLen:].min()
        elif img.ndim == 3:
            self._max = (
                img[:,:,0].flatten()[embeddedDataLen:].max(),
                img[:,:,1].flatten()[embeddedDataLen:].max(),
                img[:,:,2].flatten()[embeddedDataLen:].max(),
            )
            self._min = (
                img[:,:,0].flatten()[embeddedDataLen:].min(),
                img[:,:,1].flatten()[embeddedDataLen:].min(),
                img[:,:,2].flatten()[embeddedDataLen:].min(),
            )
        else:
            raise RuntimeError("Invalid number of dimensions image")


        # Handle image transformation
        if self.is_zoomed():
            xoffset, yoffset, width, height = self.get_zoom_region()
            endx = xoffset + width
            endy = yoffset + height
            if self.color_mode == COLOR_MODE_MONO:
                img = img[yoffset:endy, xoffset:endx]
            else:
                img = img[yoffset:endy, xoffset:endx, :]

        # Count dead pixels on ROI
        if self._pref['DPXEnabled']:
            current_img_dead_pixels = (imgArray > self._pref["DPXLimit"]).sum()
        else:
            current_img_dead_pixels = 0
        self.dead_pixels_roi.append(current_img_dead_pixels)
        self.dead_pixels_roi = self.dead_pixels_roi[-3:]

        # Record max/min pixel values on ROI
        if img.ndim == 2:
            self._maxRoi = img.flatten().max()
            self._minRoi = img.flatten().min()
        elif img.ndim == 3:
            self._maxRoi = (
                img[:,:,0].flatten().max(),
                img[:,:,1].flatten().max(),
                img[:,:,2].flatten().max(),
            )
            self._minRoi = (
                img[:,:,0].flatten().min(),
                img[:,:,1].flatten().min(),
                img[:,:,2].flatten().min(),
            )
        else:
            raise RuntimeError("Invalid number of dimensions image")

        # Auto calculate black/white levels
        if self._agc:
            black, white = np.percentile(img, [0.01, 99.99])

            if self.getGuiBlackLimits and self.getGuiWhiteLimits:
                blackMin, blackMax = self.getGuiBlackLimits()
                whiteMin, whiteMax = self.getGuiWhiteLimits()
                black = np.clip(black, blackMin, blackMax)
                white = np.clip(white, whiteMin, whiteMax)

            self.set_black(black)
            if self.updateGuiBlack is not None:
                self.updateGuiBlack(self.get_black())
            self.set_white(white)
            if self.updateGuiWhite is not None:
                self.updateGuiWhite(self.get_white())

            self._agc = False

        # Flip and rotate the image for 90 degrees (TODO: add description why)
        img = np.rot90(np.fliplr(img)).astype(npdt)

        self.calculate_profiles(img)

        self.last_displayed_image = img
        self._set_image_on_main_thread(img)

        # Frames displayed
        if not zoomUpdate:
            self.frames_displayed += 1

        # Missed frames
        current_array_id = data['uniqueId']
        if self.__last_array_id is not None and zoomUpdate == False:
            self.frames_missed += current_array_id - self.__last_array_id - 1
        self.__last_array_id = current_array_id

    def configureGuiLimits(self, dataType):
        """
        Configure the limits for the black and white settings on the GUI.

        :param dataType: (String) String representation of the incoming datatype. (E.g. 'ubyteValue')
        """
        blackMin = self.dataTypesDict[dataType]['minVal']
        blackMax = self.dataTypesDict[dataType]['maxVal']
        whiteMin = self.dataTypesDict[dataType]['minVal']
        whiteMax = self.dataTypesDict[dataType]['maxVal']

        if self.updateGuiBlackLimits is not None:
            self.updateGuiBlackLimits(blackMin, blackMax)
        if self.updateGuiWhiteLimits is not None:
            self.updateGuiWhiteLimits(whiteMin, whiteMax)

    def calculate_profiles(self, image):
        """
        Handle profile calculation.

        :param image: (nparray) Image as numpy array.
        """
        if self.image_profile_widget is not None:
            self.image_profile_widget.set_image_data(image, self.color_mode)

    def _set_image_on_main_thread(self, image):
        """Calls setImage on the same thread that Qt paintEvent is
        called on.

        Not doing this will cause race conditions
        """
        self._image_mutex.lock()
        self._image = image
        self._image_mutex.unlock()
        self._set_image_signal.emit()

    def _set_image_signal_callback(self):
        """
        Update image on the widget.

        :return: None
        """
        self._image_mutex.lock()
        levels = [self.get_black(), self.get_white()]
        self.setImage(self._image, levels = levels)
        if self.image_profile_widget is not None:
            self.image_profile_widget.plot(*self.calc_img_size_on_screen())
        self._image_mutex.unlock()
