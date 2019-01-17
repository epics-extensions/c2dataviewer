# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""

import numpy as np
import pvaccess as pva
from pvaccess import PvaException


class ScopeData:

    def __init__(self, pv=None):
        """

        :param pv:
        """
        self.pv = pv
        # self.timer = timer

        self.fps = -1
        # self.timer.timeout.connect(self.get)
        if self.pv is not None:
            self.channel = pva.Channel(self.pv)
        else:
            self.channel = None

        self.trigger = None
        self.trigger_chan = None

        self.data = None

    def get_fdr(self):
        """
        Get EPICS7 PV field description back as a list

        :return: list of FDR
        :raise PvaException: raise pvaccess exception when channel cannot be connected.
        """
        fdr = []
        if self.channel is not None:
            pv = self.channel.get('')
            for k, v in pv.getStructureDict().items():
                if type(v) == list:
                    # should epics v4 lib not have np, we "fix" it by converting list to np
                    v = np.array(v)
                    # Make type comparison compatible with PY2 & PY3
                    fdr.append(k)
                if type(v) != np.ndarray:
                    continue
                if len(v) == 0:
                    continue
            fdr.sort()

        return fdr

    def update_pv(self, name, restart=False):
        """
        Update the EPICS PV name, and test its connectivity

        :param name:
        :param restart:
        :return:
        :raise PvaException: raise pvaccess exception when channel cannot be connected.
        """
        if self.channel is not None:
            self.stop()
        if name != "":
            chan = pva.Channel(name)
            # test channel connectivity
            chan.get("field()")

            # channel connected successfully
            # update old channel information with the new one
            self.channel = chan
            self.pv = name

            # self._win.imageWidget.camera_changed()
            # self._win.imageWidget.display(self.data)
            if restart:
                self.start()
        else:
            self.channel = None

    def monitor_callback(self, data):
        """

        :param data:
        :return:
        """
        self.data = data.get()

    def start(self, routine=None):
        """

        :return:
        """

        # TODO update fps later accordingly
        if self.channel is None:
            # there is nothing to start since channel does not exist yet
            return
        try:
            if routine is None:
                self.channel.subscribe('monitorCallback', self.monitor_callback)
            else:
                self.channel.subscribe('monitorCallback', routine)
            self.channel.startMonitor('')
        except PvaException:
            raise RuntimeError("Cannot connect to PV")

    def stop(self):
        if self.channel is None:
            # there is nothing to stop since channel does not exist yet
            return
        try:
            self.channel.stopMonitor()
            self.channel.unsubscribe('monitorCallback')
        except PvaException:
            # raise RuntimeError("Fail to disconnect")
            pass

    def update_trigger(self, name, proto=None):
        """
        Update trigger PV name

        :param name:
        :return:
        """
        if self.trigger_chan is not None:
            self.stop_trigger()

        self.trigger = name
        if proto == "ca":
            # use channel access protocol
            self.trigger_chan = pva.Channel(name, pva.CA)
        else:
            # use pvAccess protocol
            self.trigger_chan = pva.Channel(name)

    def trigger_monitor_callback(self, data):
        """

        :param data:
        :return:
        """
        # TODO implement trigger support
        print(data)

    def start_trigger(self):
        """

        :return:
        """
        try:
            self.trigger_chan.subscribe('triggerMonitorCallback', self.trigger_monitor_callback)
            self.trigger_chan.startMonitor('')
        except PvaException:
            raise RuntimeError("Cannot connect to PV")

    def stop_trigger(self):
        """

        :return:
        """
        try:
            self.trigger_chan.stopMonitor()
            self.trigger_chan.unsubscribe('triggerMonitorCallback')
        except PvaException:
            # raise RuntimeError("Fail to disconnect")
            pass
