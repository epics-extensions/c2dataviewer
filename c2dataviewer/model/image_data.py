# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""

import pvaccess


class ImageData:

    def __init__(self, timer, default=None):
        """

        :param timer:
        :param default:
        """
        self.pvs = default
        self.camera = list(self.pvs.values())[0]
        self.rate = None
        self.timer = timer
        self._win = None

        self.fps = -1
        self.x, self.y = 800, 0
        self.timer.timeout.connect(self.get)

        self.data = None

    def config(self, widget):
        """

        :param widget:
        :return:
        """
        self._win = widget
        self.setCamera(list(self.pvs.values())[0])

    def setFrameRate(self, rate):
        """

        :param rate:
        :return:
        """
        self.rate = rate

    def get(self):
        try:
            self.data = self.chan.get('field()')
        except pvaccess.PvaException as e:
            return
        self._win.imageWidget.display(self.data)

    def monitorCallback(self, data):
        self.data = data
        self._win.imageWidget.display(self.data)

    def setCamera(self, name):
        self.camera = name
        self.stop()
        self.chan = pvaccess.Channel(self.camera)
        self._win.imageWidget.camera_changed()
        self.get()
        self.start()

    def setFrameRate(self, fps):
        self.fps = fps
        self.stop()
        self.start()

    def start(self):
        if self.fps == 1:
            self.timer.start(1000)
        elif self.fps == 10:
            self.timer.start(100)
        else:
            try:
                self.chan.subscribe('monitorCallback', self.monitorCallback)
                self.chan.startMonitor('')
            except pvaccess.PvaException as e:
                raise RuntimeError("Cannot connect to image PV")

    def stop(self):
        self.timer.stop()
        try:
            self.chan.stopMonitor()
            self.chan.unsubscribe('monitorCallback')
        except:
            # raise RuntimeError("Fail to disconnect")
            pass