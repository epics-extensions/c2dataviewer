# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities for image display

@author: Guobao Shen <gshen@anl.gov>
"""
import numpy as np
from pyqtgraph import QtCore
from pyqtgraph.widgets.RawImageWidget import RawImageWidget
from pvaccess import PvaException
from PyQt5.QtCore import pyqtSignal


class ImagePlotWidget(RawImageWidget):
    _set_image_signal = pyqtSignal()

    def __init__(self, parent=None, **kargs):
        RawImageWidget.__init__(self, parent=parent, scaled=True)

        self._set_image_signal.connect(self._set_image_signal_callback)
        self._image_mutex = QtCore.QMutex()

        self._noagc = kargs.get("noAGC", False)
        # self.camera_changed()
        self._agc = False
        self._lastTimestamp = None

        self.dataType = None
        self.mbReceived = 0.0
        self.framesDisplayed = 0

        # image dimension
        self.x = None
        self.y = None
        self.fps = -1

        # max value of image pixel
        self.maxVal = 0
        self.minVal = 0
        self.mutex = QtCore.QMutex()

        self._white = 255.0
        self._black = 0.0

        # Limit control to avoid overflow network for best performance
        self._pref = {"Max": 0,
                      "Min": 0,
                      "DPX": 0,
                      "DPXLimit": 0xfff0,
                      "CPU": 0,
                      "CPULimit": None,
                      "Net": 0,
                      "NetLimit": None,
                      "FPS": 0,
                      "FPSLimit": None}

        self._isInputValid = False
        self._inputType = ""
        self._df = [0]
        self._db = [0]
        self._dt = [1]
        self._dpx = [0]
        self._max = [0]
        self._min = [0]

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
            'byteValue' :   {'minVal' : int(-2**8 / 2),   'maxVal' : int(2**8 / 2 - 1),  'npdt' : "int8",   'embeddedDataLen' : 40},
            'ubyteValue' :  {'minVal' : 0           ,     'maxVal' : int(2**8 - 1),      'npdt' : "uint8",  'embeddedDataLen' : 40},
            'shortValue' :  {'minVal' : int(-2**16 / 2),  'maxVal' : int(2**16 / 2 - 1), 'npdt' : "int16",  'embeddedDataLen' : 20},
            'ushortValue' : {'minVal' : 0               , 'maxVal' : int(2**16 - 1),     'npdt' : "uint16", 'embeddedDataLen' : 20},
            'intValue' :    {'minVal' : int(-2**32 / 2),  'maxVal' : int(2**32 / 2 - 1), 'npdt' : "int32",  'embeddedDataLen' : 0},
            'uintValue' :   {'minVal' : 0               , 'maxVal' : int(2**32 - 1),     'npdt' : "uint32", 'embeddedDataLen' : 0},
            'longValue' :   {'minVal' : int(-2**64 / 2),  'maxVal' : int(2**64 / 2 - 1), 'npdt' : "int64",  'embeddedDataLen' : 0},
            'ulongValue' :  {'minVal' : 0               , 'maxVal' : int(2**64 - 1),     'npdt' : "uint64", 'embeddedDataLen' : 0},
            'floatValue' :  {'minVal' : int(-2**24),      'maxVal' : int(2**24),         'npdt' : "float32",'embeddedDataLen' : 0},
            'doubleValue' : {'minVal' : int(-2**53),      'maxVal' : int(2**53),         'npdt' : "float64",'embeddedDataLen' : 0},
        }

        self.timer = kargs.get("timer", QtCore.QTimer())

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
            self.__update_dimension(self.datasource.get())
            self.timer.timeout.connect(self.get)

    def __update_dimension(self, data):
        """

        :param data:
        :return:
        """
        dims = data['dimension']
        x = dims[0]
        y = dims[1]
        if (x != self.x) or (y != self.y):
            self.x = x['size']
            self.y = y['size']

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
        if self.fps == -1:
            self.datasource.start(routine=self.monitor_callback)
        else:
            self.timer.start(1000/self.fps)

    def stop(self):
        """

        :return:
        """
        self.timer.stop()
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
        except PvaException as e:
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
            self.__update_dimension(self.datasource.get())
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

    def display(self, data):
        """
        Display and update image using data received

        :param data:
        :return:
        """

        # Determinate input data type
        data_types = data['value'][0].keys()
        assert len(list(data_types)) == 1
        inputType = list(data_types)[0]

        # Check if the input is valid
        if not inputType in self.dataTypesDict:
            self._isInputValid = False
            raise RuntimeError('No recognized image data received.')
        else:
            self._isInputValid = True


        # Lookup required infomartion for the current input type
        i = data['value'][0][inputType]
        sz = i.nbytes
        maxVal = self.dataTypesDict[inputType]['maxVal']
        minVal = self.dataTypesDict[inputType]['minVal']
        npdt = self.dataTypesDict[inputType]['npdt']
        embeddedDataLen = self.dataTypesDict[inputType]['embeddedDataLen']

        # Configure GUI for the correct type
        if inputType != self._inputType:
            self.configureGuiLimits(inputType)

        self._inputType = inputType

        # Get image statistics
        if maxVal != self.maxVal:
            self.maxVal = maxVal
        if minVal != self.minVal:
            self.minVal = minVal

        self.mbReceived += sz/1024.0/1024.0

        ts = data['timeStamp']
        if ts == self._lastTimestamp:
            # if timstamp hasn't changed, its not a new image
            return
        self._lastTimestamp = ts

        # count dead pixels
        # TODO: Dead pixel count was requested for the specific type of the camera,
        # as the DPXLimit is hardcoded value to 0xfff0. Consequently all all pixels
        # on the cameras with image depth higher than UInt16 can be counted as dead.
        # Discussion about this is on the Gitlab: https://git.aps.anl.gov/C2/conda/data-viewer/-/merge_requests/17
        dpx = (i[embeddedDataLen:] > self._pref["DPXLimit"]).sum()
        self._dpx.append(dpx)
        self._dpx = self._dpx[-3:]

        # record max/min pixel values
        self._max.append(i[embeddedDataLen:].max())
        self._max = self._max[-3:]
        self._min.append(i[embeddedDataLen:].min())
        self._min = self._min[-3:]

        # resize to get a 2D array from 1D data structure
        if self.x == 0 or self.y == 0:
            # return
            raise RuntimeError("Image dimension not initialized")
        i = np.resize(i, (self.y, self.x))

        if self._agc:
            black, white = np.percentile(i, [0.01, 99.99])

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
        i = np.rot90(np.fliplr(i)).astype(npdt)

        self._set_image_on_main_thread(i)

        self.framesDisplayed += 1

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
        self._image_mutex.unlock()
