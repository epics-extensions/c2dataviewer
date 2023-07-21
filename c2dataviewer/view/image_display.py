# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities for image display

@author: Guobao Shen <gshen@anl.gov>
"""
from collections import namedtuple
import queue
import logging

import numpy as np
from pyqtgraph import QtCore
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.widgets.RawImageWidget import RawImageWidget
import blosc
import pvaccess as pva

from .image_definitions import *
from .image_profile_display import ImageProfileWidget

class ImageCompressionUtility:

    NUMPY_DATA_TYPE_MAP = {
        pva.UBYTE   : np.dtype('uint8'),
        pva.BYTE    : np.dtype('int8'),
        pva.USHORT  : np.dtype('uint16'),
        pva.SHORT   : np.dtype('int16'),
        pva.UINT    : np.dtype('uint32'),
        pva.INT     : np.dtype('int32'),
        pva.ULONG   : np.dtype('uint64'),
        pva.LONG    : np.dtype('int64'),
        pva.FLOAT   : np.dtype('float32'),
        pva.DOUBLE  : np.dtype('float64')
    }
    
    NTNDA_DATA_TYPE_MAP = {
        pva.UBYTE   : 'ubyteValue',
        pva.BYTE    : 'byteValue',
        pva.USHORT  : 'ushortValue',
        pva.SHORT   : 'shortValue',
        pva.UINT    : 'uintValue',
        pva.INT     : 'intValue',
        pva.ULONG   : 'ulongValue',
        pva.LONG    : 'longValue',
        pva.FLOAT   : 'floatValue',
        pva.DOUBLE  : 'doubleValue',
    }

    @classmethod
    def get_ntnda_data_type(cls, pvaType):
       return cls.NTNDA_DATA_TYPE_MAP.get(pvaType)

    @classmethod
    def get_decompressor(cls, codecName):
        utilityMap = {
            'blosc' : cls.blosc_decompress
        }
        decompressor = utilityMap.get(codecName)
        if not decompressor:
            raise RuntimeError(f'Unsupported compression: {codecName}')
        return decompressor

    @classmethod
    def blosc_decompress(cls, inputArray, inputType, uncompressedSize):
        oadt = cls.NUMPY_DATA_TYPE_MAP.get(inputType) 
        oasz = uncompressedSize // oadt.itemsize
        outputArray = np.empty(oasz, dtype=oadt)
        nBytesWritten = blosc.decompress_ptr(bytearray(inputArray), outputArray.__array_interface__['data'][0])
        return outputArray

class MouseDialog:
    def __init__(self, imageWidget):
        # mouse dialog flags
        self.is_mouse_clicked = False
        self.mouse_dialog_enabled = False
        self.mouse_dialog_launched = False
        
        self.max_textbox_width = 0

        # pixel coordinates
        self.pix_x = 0
        self.pix_y = 0

        # textbox coordinates inside the widget screen
        self.x_coor = 0
        self.y_coor = 0

        # intensity coordinates
        self.int_x = 0
        self.int_y = 0

        # initialize mouse dialog widgets
        self.layout = QtWidgets.QVBoxLayout(imageWidget)
        self.textbox = QtWidgets.QTextEdit(imageWidget)
        self.textbox.setFixedSize(0,0)

    def enable_mouse_dialog(self):
        self.mouse_dialog_enabled = True
        self.is_mouse_clicked = False

    def disable_mouse_dialog(self):
        self.mouse_dialog_enabled = False
        self.mouse_dialog_launched = False
        self.is_mouse_clicked = False
        self.textbox.setFixedSize(0,0)
    

Image = namedtuple("Image", ['id', 'new', 'image', 'black', 'white'])
class ImagePlotWidget(RawImageWidget):

    MIN_DISPLAY_QUEUE_SIZE = 0
    MAX_DISPLAY_QUEUE_SIZE = 999
    DEFAULT_DISPLAY_QUEUE_SIZE = 20
    ZOOM_LENGTH_MIN = 4 # Using zoom this is the smallest number of pixels to display in each direction

    _set_image_signal = QtCore.pyqtSignal()
    connection_changed_signal = QtCore.Signal(str, str)
    
    def __init__(self, parent=None, **kargs):
        RawImageWidget.__init__(self, parent=parent, scaled=True)

        self._set_image_signal.connect(self._set_image_signal_callback)

        self._noagc = kargs.get("noAGC", False)
        # self.camera_changed()
        self._agc = False
        self._lastTimestamp = None
        self._freeze = False

        self.__last_array_id = None
        self.dataType = None
        self.MB_received = 0.0
        self.frames_received = 0
        self.frames_displayed = 0
        self.frames_missed = 0

        # Image properties
        self.dimensions = None
        self.color_mode = None
        self.x = None
        self.y = None
        self.z = None

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
        self.__zoomSelectionIndicator = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
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

        # Queue used to transfer the images from the process to the display thread
        self.draw_queue = queue.Queue(ImagePlotWidget.DEFAULT_DISPLAY_QUEUE_SIZE)

        # mouse dialog box
        self.mouse_dialog = MouseDialog(self)

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
        # Flag to indicate click occured
        self.mouse_dialog.is_mouse_clicked = True

        # Get location of the click
        click_position = event.pos()
        x_position = click_position.x()
        y_position = click_position.y()

        # Check if the press happened on the image
        img_width, img_height, _ = self.calc_img_size_on_screen()
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
        if self.mouse_dialog.mouse_dialog_enabled:
            self.updateMouseDialog(event)

        # Mouse is moving, while selecting roi. Redraw the selection rectangle.
        if self.roi_origin is not None and self.mouse_dialog.is_mouse_clicked:
            self.__zoomSelectionIndicator.setGeometry(
                QtCore.QRect(self.roi_origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        """
        This method is event handler for the mouse button release event and is called by the Qt framework.

        :param event: (QMouseEvent) Parameter holding event details.
        :return: (None)
        """
        # Flag to indicate click over
        self.mouse_dialog.is_mouse_clicked = False

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

    def updateMouseDialog(self, event):
        """
        This method continuously displays and updates the dialog box beneath the mouse cursor.

        :param event: (QMouseEvent) Parameter holding event details.
        :return: (None)
        """
        # Return if there is no image data
        if self.__zoomDict['width'] == 0 and self.__zoomDict['height'] == 0:
            return
        
        # Flag to indicate mouse dialog has been launched
        self.mouse_dialog.mouse_dialog_launched = True
        
        # Get the current image size on screen
        img_width, img_height, pixel_size = self.calc_img_size_on_screen()

        # Get the current mouse position on the widget
        mouse_position = event.pos()

        # Get zoom parameters
        xOffset, yOffset, width, height = self.get_zoom_region()

        # Calculate pixel coordinates
        self.mouse_dialog.pix_x = int(mouse_position.x()//pixel_size) + xOffset
        self.mouse_dialog.pix_y = int(mouse_position.y()//pixel_size) + yOffset
        if self.mouse_dialog.pix_x >= xOffset + width:
            self.mouse_dialog.pix_x = xOffset + width - 1
        if self.mouse_dialog.pix_y >= yOffset + height:
            self.mouse_dialog.pix_y = yOffset + height - 1

        # Update the textbox location inside the widget screen as the mouse moves
        self.mouse_dialog.x_coor = mouse_position.x()+5
        self.mouse_dialog.y_coor = mouse_position.y()+10
        
        # Calculate the intensity coordinates corrected for zoom
        self.mouse_dialog.int_x = self.mouse_dialog.pix_x - xOffset
        self.mouse_dialog.int_y = self.mouse_dialog.pix_y - yOffset

        # Set the dialog box paramters
        self.setup_mouse_textbox()

        # Flip the textbox location when approaching image widget screen boundary
        if (mouse_position.x() >= (width * pixel_size - self.mouse_dialog.max_textbox_width)):
            self.mouse_dialog.x_coor = self.mouse_dialog.x_coor - self.mouse_dialog.max_textbox_width - 20
        if (mouse_position.y() >= (height * pixel_size - 50)):
            self.mouse_dialog.y_coor = self.mouse_dialog.y_coor - 55
        
        # Set layout
        self.mouse_dialog.layout.setContentsMargins(self.mouse_dialog.x_coor, self.mouse_dialog.y_coor,int(img_width), int(img_height))
        self.mouse_dialog.layout.addWidget(self.mouse_dialog.textbox)

    def setup_mouse_textbox(self):
        """
        This method set the mouse textbox size and text within based on the image color and data type.

        """
        if self.color_mode == COLOR_MODE_MONO:
            # Get the monochromatic intensity value at the particular pixel and display in the correct format
            try:
                self.intensity = self.last_displayed_image.image[self.mouse_dialog.int_x][self.mouse_dialog.int_y]
                if self.intensity >= 999999:
                    self.intensity = "{:e}".format(self.intensity)
                self.mouse_dialog.textbox.setText(f"({self.mouse_dialog.pix_x}, {self.mouse_dialog.pix_y})\nI: {self.intensity}")
                # Set textbox size
                if (self.mouse_dialog.textbox.fontMetrics().boundingRect(self.mouse_dialog.textbox.toPlainText()).width() > self.mouse_dialog.max_textbox_width):
                    self.mouse_dialog.max_textbox_width = self.mouse_dialog.textbox.fontMetrics().boundingRect(self.mouse_dialog.textbox.toPlainText()).width()
                self.mouse_dialog.textbox.setFixedSize(self.mouse_dialog.max_textbox_width+5, 45)
            except Exception as e:
                logging.getLogger().error('Error displaying mouse dialog: %s', str(e))
        else:
            # Get the RGB intensity values at the particular pixel and display in the correct format
            try:
                r_intensity = self.last_displayed_image.image[self.mouse_dialog.int_x][self.mouse_dialog.int_y][0]
                if r_intensity >= 999999:
                    r_intensity = "{:e}".format(r_intensity)
                g_intensity = self.last_displayed_image.image[self.mouse_dialog.int_x][self.mouse_dialog.int_y][1]
                if g_intensity >= 999999:
                    g_intensity = "{:e}".format(g_intensity)
                b_intensity = self.last_displayed_image.image[self.mouse_dialog.int_x][self.mouse_dialog.int_y][2]
                if b_intensity >= 999999:
                    b_intensity = "{:e}".format(b_intensity)
                
                # Set textbook text and size
                if self._inputType == 'ubyteValue' or self._inputType == 'byteValue' or self._inputType == 'ushortValue' or self._inputType == 'shortValue':
                    self.mouse_dialog.textbox.setText(f"({self.mouse_dialog.pix_x}, {self.mouse_dialog.pix_y})\nR: {r_intensity}, G: {g_intensity}, B: {b_intensity}")
                    if (self.mouse_dialog.textbox.fontMetrics().boundingRect(self.mouse_dialog.textbox.toPlainText()).width() > self.mouse_dialog.max_textbox_width):
                        self.mouse_dialog.max_textbox_width = self.mouse_dialog.textbox.fontMetrics().boundingRect(self.mouse_dialog.textbox.toPlainText()).width()
                    self.mouse_dialog.textbox.setFixedSize(self.mouse_dialog.max_textbox_width+5, 45)
                else:
                    self.mouse_dialog.textbox.setText(f"({self.mouse_dialog.pix_x}, {self.mouse_dialog.pix_y})\nR: {r_intensity}")
                    if (self.mouse_dialog.textbox.fontMetrics().boundingRect(self.mouse_dialog.textbox.toPlainText()).width() > self.mouse_dialog.max_textbox_width):
                        self.mouse_dialog.max_textbox_width = self.mouse_dialog.textbox.fontMetrics().boundingRect(self.mouse_dialog.textbox.toPlainText()).width()
                    self.mouse_dialog.textbox.setText(f"({self.mouse_dialog.pix_x}, {self.mouse_dialog.pix_y})\nR: {r_intensity},\nG: {g_intensity},\nB: {b_intensity}")
                    self.mouse_dialog.textbox.setFixedSize(self.mouse_dialog.max_textbox_width+5, 85)
            except Exception as e:
                logging.getLogger().error('Error displaying mouse dialog: %s', str(e))


    def set_display_queue_size(self, new_size):
        """
        Change display queue max size.

        :param int new_size: Set queue size. Valid values are >=0.
        """

        if not isinstance(new_size, int) or new_size < 0:
            return

        self.draw_queue.maxsize = new_size
        while self.draw_queue.qsize() > new_size:
            try:
                self.draw_queue.get_nowait()
            except queue.Empty:
                break

    def get_display_max_queue_size(self):
        """
        Get queue max size.
        """
        return self.draw_queue.maxsize

    def get_display_queue_size(self):
        """
        Get current display queue size.
        """
        return self.draw_queue.qsize()

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
            try:
                self.display(self.data, zoomUpdate=True)
            except Exception as e:
                logging.getLogger().error('Error displaying data: %s', str(e))

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
            try:
                self.display(self.data, zoomUpdate=True)
            except Exception as e:
                logging.getLogger().error('Error displaying data: %s', str(e))

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

        return image_width, image_height, pixel_size

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
        
    def __update_dimension(self, data):
        """

        :param data:
        :return:
        """

        try:
            # Get dimensions
            dims = data['dimension']
            self.dimensions = len(dims)
        

            # Get color mode
            attributes = data['attribute']
            if any(('name' in attr and attr['name'] == "ColorMode") for attr in attributes ):
                for attribute in attributes:
                    if attribute['name'] == "ColorMode":
                        self.color_mode = attribute['value'][0]['value']
            else:
                raise RuntimeError(f"NDArray does not contain ColorMode Attribute.")
        except:
            if self.dimensions == 2:
                self.color_mode = COLOR_MODE_MONO
            else:
                raise
            
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
            raise RuntimeError(f"Invalid data/color mode data. dimensions=%r, colormode=%r" % (self.dimensions, self.color_mode) )

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
            self.datasource.start(routine=self.data_callback,
                                  status_callback=self.connection_changed_signal.emit)
            
    def stop(self):
        """

        :return:
        """
        try:
            if self.datasource is not None:
                self.datasource.stop()
        except RuntimeError as e:
            logging.getLogger().debug('Error stopping source: ' + str(e))

    def set_framerate(self, value):
        """

        :param value:
        :return:
        """
        self.wait()
        self.stop()
        if value == -1:
            value = None
            
        self.datasource.update_framerate(value)
        self.start()
        self.signal()
        
    def data_callback(self, data):
        """

        :param data:
        :return:
        """
        self.data = data
        self.wait()
        try:
            self.display(self.data)
        except Exception as e:
            logging.getLogger().error('Error displaying data: %s', str(e))
        finally:
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
            self.datasource.update_device(value, test_connection=False)
        except pva.PvaException as e:
            # TODO wrap PvaException from pvaPy in a better way for other interface
            # pvAccess connection error
            # release mutex lock
            self.signal()
            # NOTE: data source is already stopped on error. calling stop here will override
            # the connection status
            #self.stop()
            raise RuntimeError(str(e))

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
        # Count received frames
        if not zoomUpdate:
            self.frames_received += 1

        # Check if the queue is full
        if self.draw_queue.full() and not zoomUpdate:
            return

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
        codecName = data['codec']['name']

        # Check if image size is zero
        if imgArray.size == 0:
            raise RuntimeError('Image size cannot be zero.')
        
        if codecName:
            uncompressedSize = data['uncompressedSize']
            uncompressedType = data['codec.parameters'][0]['value']
            decompress = ImageCompressionUtility.get_decompressor(codecName)
            imgArray = decompress(imgArray, uncompressedType, uncompressedSize)
            inputType = ImageCompressionUtility.get_ntnda_data_type(uncompressedType)
       
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

        # Missed frames
        current_array_id = data['uniqueId']
        if self.__last_array_id is not None and zoomUpdate == False:
            self.frames_missed += current_array_id - self.__last_array_id - 1
        self.__last_array_id = current_array_id

        image = Image(current_array_id,
                      not zoomUpdate,
                      img.copy(),
                      self.get_black(),
                      self.get_white())

        # Put the image on the queue and emit the signal
        self.draw_queue.put(image)
        self._set_image_signal.emit()

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

    def _set_image_signal_callback(self):
        """
        Update image on the widget.

        :return: None
        """
        image = self.draw_queue.get()
        levels = [image.black, image.white]
        self.setImage(image.image, levels = levels)
        if self.image_profile_widget is not None:
            img_width, img_height, _ = self.calc_img_size_on_screen()
            self.image_profile_widget.plot(img_width, img_height)
        if image.new:
            self.frames_displayed += 1
        self.last_displayed_image = image

        # If the mouse dialog has been launched, update the intensity value with every image update
        if (self.mouse_dialog.mouse_dialog_launched):
            # Set the dialog box paramters
            self.setup_mouse_textbox()

            # Set layout
            self.mouse_dialog.layout.addWidget(self.mouse_dialog.textbox)