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
        
        self._gain = 1.0
        self._black = 0.0

        self._noagc = kargs.get("noAGC", False)
        # self.camera_changed()
        self._agc = False
        self._lastTimestamp = None

        self.mbReceived = 0.0
        self.framesDisplayed = 0

        # image dimension
        self.x = None
        self.y = None
        self.fps = -1

        # max value of image pixel
        self.maxVal = 0
        self.mutex = QtCore.QMutex()

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

        self._df = [0]
        self._db = [0]
        self._dt = [1]
        self._dpx = [0]
        self._max = [0]
        self._min = [0]

        self._scaling = 1.0
        self._agc = True
        self._lastTimestamp = None

        # Gain controller slider widget
        self.slider = None
        self.gain = None

        self.datasource = None
        self.data = None

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

    def set_gain(self, value):
        """

        :param value:
        :return:
        """
        self._gain = value

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

    def enable_auto_gain(self):
        """
        Enable auto gain calibration for image

        :return:
        """
        self._agc = True

    def gain_controller(self, slider, gain):
        """

        :return:
        """
        self.slider = slider
        self.gain = gain

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
        data_types = data['value'][0].keys()
        if 'ushortValue' in data_types:
            i = data['value'][0]['ushortValue']
            sz = i.nbytes
            maxVal = 65535
            npdt = 'uint16'
            embeddedDataLen = 20
        elif 'ubyteValue' in data_types:
            i = data['value'][0]['ubyteValue']
            sz = i.nbytes
            maxVal = 255
            npdt = 'uint8'
            embeddedDataLen = 40
        else:
            self.stop()
            raise RuntimeError('No recognized image data received.')

        # self.__update_dimension(data)

        if maxVal != self.maxVal:
            self.maxVal = maxVal
        self.mbReceived += sz/1024.0/1024.0

        ts = data['timeStamp']
        if ts == self._lastTimestamp:
            # if timstamp hasn't changed, its not a new image
            return
        self._lastTimestamp = ts

        # count dead pixels
        dpx = (i[embeddedDataLen:] > self._pref["DPXLimit"]).sum()
        self._dpx.append(dpx)
        self._dpx = self._dpx[-3:]

        # self._win.deadPixel.updateDeadPixels(dpx)

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
            self._black, white = np.percentile(i, [0.01, 99.99])
            self.slider.setValue(self._black)
            if (white - self._black) == 0.0:
                self._gain = 1.0
            else:
                self._gain = maxVal / (white - self._black)
            self.gain.setValue(self._gain * 10.0)
            self._agc = False

        # adjust black point and gain
        if self._black > 0 or self._gain != 1.0:
            i = (np.clip(i, self._black, maxVal) - self._black) * self._gain
            i = np.clip(i, 0, maxVal).astype(npdt)
        i = np.rot90(np.fliplr(i))
        
        self._set_image_on_main_thread(i)

        self.framesDisplayed += 1

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
        self._image_mutex.lock()
        self.setImage(self._image)
        self._image_mutex.unlock()
