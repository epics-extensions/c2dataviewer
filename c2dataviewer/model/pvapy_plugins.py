# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities using pvaPy as pvAccess binding

@author: Guobao Shen <gshen@anl.gov>
"""
import time
from threading import Lock
from collections import deque
from statistics import mean
import enum

import pvaccess as pva
from pvaccess import PvaException

class PollStrategy:
    def __init__(self, context, timer):
        self.ctx = context
        self.timer = timer
        self.timer.timeout.connect(self.poll)
        
    def _data_callback(self, data):
        self.ctx.data_callback_wrapper(data)

    def poll(self):
        try:
            self.data = self.ctx.get()
        except PvaException:
            self.stop()

        #locks needed?
        self._data_callback(self.data)
            
        
    def start(self):
        self.timer.start(1000/self.ctx.rate)

    def stop(self):
        self.timer.stop()
    
class MonitorStrategy:
    def __init__(self, context):
        self.ctx = context
        
    def _data_callback(self, data):
        self.ctx.data_callback_wrapper(data)

    def start(self):
        try:
            self.ctx.channel.subscribe('monitorCallback', self._data_callback)
            self.ctx.channel.startMonitor('')
        except PvaException:
            raise RuntimeError('Cannot connect to PV ({})'.format(self.ctx.name))
        
    def stop(self):
        try:
            self.ctx.channel.stopMonitor()
            self.ctx.channel.unsubscribe('monitorCallback')
        except PvaException:
            pass
    
class Channel:
    ALL_FIELDS = 'field()'
    
    class State(enum.Enum):
        CONNECTED = 1
        CONNECTING = 2
        DISCONNECTING = 3
        DISCONNECTED = 4
        FAILED_TO_CONNECT = 5

    def __init__(self, name, timer):
        self.channel = pva.Channel(name)
        self.name = name
        self.rate = None
        self.data_callback = None
        self.data = None
        self.monitor_strategy = MonitorStrategy(self)
        self.poll_strategy = PollStrategy(self, timer)
        self.strategy = None
        self.rate = None

    def data_callback_wrapper(self, data):
        if self.data_callback:
            self.data_callback(data)
        else:
            self.data = data.get()

    def start(self, routine=None, rate=None):
        self.data_callback = routine
        self.rate = rate
        self.strategy = self.poll_strategy if self.rate else self.monitor_strategy
        self.strategy.start()

    def stop(self):
        if self.strategy:
            self.strategy.stop()
        
    def get(self):
        return self.channel.get('')

class DataSource:
    def __init__(self, timer_factory, default=None):
        """

        :param default:
        """
        # local cache of latest data
        self.data = None
        # EPICS7 channel
        self.channel = None
        self.fps = None
        self.timer_factory = timer_factory
        
        # Default PV name
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
        self.channel = Channel(self.device, self.timer_factory())
        self.get()

    def get(self, field=None):
        """
        Get data of given field name.
        If field is None, get whole EPICS7 record data from current EPICS7 channel.

        :param field: EPICS7 field name
        :return:
        """
        if self.channel is None:
            return None

        return self.channel.get()

    def update_framerate(self, fps):
        self.fps = fps
        
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
            chan = Channel(name, self.timer_factory())
            # test channel connectivity
            chan.get()

            # channel connected successfully
            # update old channel information with the new one
            self.channel = chan
            self.device = name

            if restart:
                self.start()
        else:
            self.channel = None

    def start(self, routine=None):
        """
        Start a EPICS7 monitor for current device.

        :return:
        :raise PvaException: raise pvaccess exception when channel cannot be connected.
        """
        if self.channel is None:
            return

        self.channel.start(routine=routine, rate=self.fps)

    def stop(self):
        """
        Stop monitor EPICS7 channel for current device.

        :return:
        :raise PvaException: raise pvaccess exception when channel fails to disconnect.
        """
        if self.channel is None:
            return

        self.channel.stop()

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
        if trigger_rec_type not in ["bi", "bo", "ai", "ao", "longin", "longout", "calc", "event"]:
            if self.trigger_chan is not None:
                self.trigger = None
                self.trigger_chan = None
            raise RuntimeError("Trigger record has to be one in [ai, ao, bi, bo, calc, longin, longout, event]")

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
            self.trigger_chan.startMonitor('field(timeStamp,value)')
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
