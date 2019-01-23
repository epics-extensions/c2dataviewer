# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""

import pvaccess


class ImageData:

    def __init__(self, default=None):
        """

        :param timer:
        :param default:
        """
        self.data = None
        self.chan = None
        self.x, self.y = 800, 0

        self.pvs = default
        if self.pvs is not None:
            self.camera = list(self.pvs.values())[0]
            self.setCamera(self.camera)

    def monitorCallback(self, data):
        """

        :param data:
        :return:
        """
        self.data = data

    def get(self, field=None):
        """

        :return:
        """
        if field is None:
            data = self.chan.get('field()')
        else:
            data = self.chan.get(field)
        return data

    def setCamera(self, name):
        self.camera = name
        self.chan = pvaccess.Channel(self.camera)
        self.get()

    def start(self, routine=None):
        """
        Start pvAccess monitor. The callback could be user specified, or the one in the data source

        :param routine:
        :return:
        """
        try:

            if self.chan is not None:
                if routine is None:
                    self.chan.subscribe('monitorCallback', self.monitorCallback)
                else:
                    self.chan.subscribe('monitorCallback', routine)
                self.chan.startMonitor('')
        except pvaccess.PvaException:
            raise RuntimeError("Cannot connect to image PV")

    def stop(self):
        """
        Stop pvAccess monitor

        :return:
        """
        try:
            if self.chan is not None:
                self.chan.stopMonitor()
                self.chan.unsubscribe('monitorCallback')
        except pvaccess.PvaException:
            # raise RuntimeError("Fail to disconnect")
            # TODO handle exception in better way, and add logging information
            pass
