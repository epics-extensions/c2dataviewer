# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities using pvaPy as pvAccess binding

@author: Guobao Shen <gshen@anl.gov>
"""

import numpy as np
import pvaccess as pva
from pvaccess import PvaException


class DataSource:
    def __init__(self, default=None):
        """

        :param default:
        """
        # local cache of latest data
        self.data = None
        # EPICS7 channel
        self.channel = None

        # default PV name
        self.device = None
        if default is not None:
            if type(default) in [list, tuple]:
                self.__init_connection(default[0])
            elif type(default) == dict:
                self.__init_connection(list(default.values())[0])
            elif type(default) == str:
                self.__init_connection(default)
            else:
                raise RuntimeError("Unknown data type of default parameter: ", default)

        # trigger support from external EPICS3/7 channel
        self.trigger = None
        self.trigger_chan = None

    def __init_connection(self, name):
        """
        Create initial channel connection with given PV name

        :param name: EPICS7 PV name
        :return:
        """
        self.device = name
        self.channel = pva.Channel(self.device)
        self.get()

    def get(self, field=None):
        """
        Get data of given field name.
        If field is None, get whole EPICS7 record data from current EPICS7 channel.

        :param field: EPICS7 field name
        :return:
        """
        if field is None:
            data = self.channel.get('field()')
        else:
            data = self.channel.get(field)
        return data

    def get_fdr(self):
        """
        Get EPICS7 PV field description back as a list

        :return: list of field description
        :raise PvaException: raise pvaccess exception when channel cannot be connected.
        """
        fdr = []
        fdr_scalar = []
        if self.channel is not None:
            pv = self.channel.get('')
            for k, v in pv.getStructureDict().items():
                if type(v) == list:
                    # should epics v4 lib not have np, we "fix" it by converting list to np
                    v = np.array(v)
                    # Make type comparison compatible with PY2 & PY3
                    fdr.append(k)
                elif type(v) == pva.ScalarType:
                    fdr_scalar.append(k)
                if type(v) != np.ndarray:
                    continue
                if len(v) == 0:
                    continue
            fdr.sort()
            fdr_scalar.sort()

        return fdr, fdr_scalar

    def update_device(self, name, restart=False):
        """
        Update device, EPICS PV name, and test its connectivity

        :param name: device name
        :param restart: flag to restart or not
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
            self.device = name

            if restart:
                self.start()
        else:
            self.channel = None

    def monitor_callback(self, data):
        """
        Default call back routine for EPICS7 channel of current device.
        It updates the data with the latest value.

        :param data: new data from EPICS7 channel
        :return:
        """
        self.data = data.get()

    def start(self, routine=None):
        """
        Start a EPICS7 monitor for current device.

        :return:
        :raise PvaException: raise pvaccess exception when channel cannot be connected.
        """
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
            raise RuntimeError("Cannot connect to EPICS7 PV ({})".format(self.device))

    def stop(self):
        """
        Stop monitor EPICS7 channel for current device.

        :return:
        :raise PvaException: raise pvaccess exception when channel fails to disconnect.
        """
        if self.channel is None:
            # there is nothing to stop since channel does not exist yet
            return
        try:
            self.channel.stopMonitor()
            self.channel.unsubscribe('monitorCallback')
        except PvaException:
            # raise RuntimeError("Fail to disconnect EPICS7 PV ({})".format(self.device))
            pass

    def update_trigger(self, name, proto='ca'):
        """
        Update trigger PV name

        :param name: PV name for external trigger
        :param proto: protocol, should be 'pva' or 'ca'. 'ca' by default
        :return:
        """
        if self.trigger_chan is not None:
            self.stop_trigger()

        if name == self.trigger:
            # nothing change
            return

        if proto.lower() == "ca":
            # use channel access protocol, which is default
            trigger_chan = pva.Channel(name, pva.CA)
        elif proto.lower() == "pva":
            # use pvAccess protocol
            trigger_chan = pva.Channel(name)
        else:
            raise RuntimeError("Unknown EPICS communication protocol {}".format(proto))

        # test connectivity, which might cause for example timeout exception
        trigger_chan.get("")

        # test the record type.
        # For the first implementation, it accepts bi/bo
        trigger_rec_type = pva.Channel(name+".RTYP", pva.CA).get()["value"]
        if trigger_rec_type not in ["bi", "bo", "ai", "ao", "longin", "longout", "calc"]:
            if self.trigger_chan is not None:
                self.trigger = None
                self.trigger_chan = None
            raise RuntimeError("Trigger record has to be one in [ai, ao, bi, bo, calc, longin, longout]")

        # update trigger name & channel
        self.trigger = name
        self.trigger_chan = trigger_chan
        return trigger_rec_type

    def trigger_monitor_callback(self, data):
        """

        :param data:
        :return:
        """
        # TODO implement trigger support
        # print(data)

    def start_trigger(self, routine=None):
        """

        :return:
        """
        try:
            if routine is None:
                self.trigger_chan.subscribe('triggerMonitorCallback', self.trigger_monitor_callback)
            else:
                self.trigger_chan.subscribe('triggerMonitorCallback', routine)
            self.trigger_chan.startMonitor('field()')
        except PvaException:
            raise RuntimeError("Cannot connect to PV {}".format(self.trigger))

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
