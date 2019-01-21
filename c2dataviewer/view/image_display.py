# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities for image display

@author: Guobao Shen <gshen@anl.gov>
"""

import numpy as np
from pyqtgraph.widgets.RawImageWidget import RawImageWidget
import cv2


class ImagePlotWidget(RawImageWidget):
    def __init__(self, parent=None, **kargs):
        RawImageWidget.__init__(self, parent=parent)
        self._gain = 1.0
        self._black = 0.0

        self._noagc = kargs.get("noAGC", False)
        self.camera_changed()

        self.mbReceived = 0.0
        self.framesDisplayed = 0

        # image dimension
        self.x = 0
        self.y = 0

        # max value of image pixel
        self.maxVal = 0

        # Limit control to avoid overflow network for best performance
        self._pref={}
        self._pref["Max"] = 0
        self._pref["Min"] = 0
        self._pref["DPX"] = 0
        self._pref["DPXLimit"] = 0xfff0
        self._pref["CPU"] = 0
        self._pref["CPULimit"] = 30
        self._pref["Net"] = 0
        self._pref["NetLimit"] = 20
        self._pref["FPS"] = 0
        self._pref["FPSLimit"] = 0.1

        self._df = [0]
        self._db = [0]
        self._dt = [1]
        self._dpx = [0]
        self._max = [0]
        self._min = [0]

        self._scaling = 1.0

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

    def camera_changed(self):
        """

        :return:
        """
        self._agc = False
        self._lastTimestamp = None

    def enable_auto_gain(self):
        """
        Enable auto gain calibration for image

        :return:
        """
        self._agc = True

    def gaincontroller(self, slider, gain):
        """

        :return:
        """
        self.slider = slider
        self.gain = gain

    def set_scaling(self, scale):
        """

        :param scale:
        :param x:
        :param y:
        :return:
        """
        self._scaling = scale

    def display(self, data):
        """
        Display and update image using data received

        :param data:
        :return:
        """

        # if not self.initialized:
        #     print("not initialized yet")
        #     return

        # print("Why no image?")
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
            # self._win.setStatus('No recognized image data received.')
            # return
            raise RuntimeError('No recognized image data received.')

        x, y = data['dimension']
        if (x != self.x) or (y != self.y):
            self.x = x['size']
            self.y = y['size']

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
        i = cv2.resize(i, dsize=(int(self.x * self._scaling), int(self.y * self._scaling)),
                       interpolation=cv2.INTER_AREA)

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
        i = (np.clip(i, self._black, maxVal) - self._black) * self._gain
        i = np.clip(i, 0, maxVal).astype(npdt)

        self.setImage(np.rot90(np.fliplr(i)))
        # self._win._app.processEvents()

        self.framesDisplayed += 1

        return self._black, self._gain