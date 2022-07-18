# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""

import numpy as np
import pyqtgraph
import pvaccess as pva
from ..model import ConnectionState
from .scope_controller_base import ScopeControllerBase
from ..view.scope_display import PlotChannel as ScopePlotChannel
from pyqtgraph.Qt import QtCore
import math
import statistics

class ScopeController(ScopeControllerBase):

    def __init__(self, widget, model, parameters, **kwargs):
        
        """

        :param model:
        :param parameters:
        :param channels:
        """
        self.color_pattern = kwargs.get("color", 
                                        ['#FFFF00', '#FF00FF', '#55FF55', '#00FFFF', '#5555FF',
                                         '#5500FF', '#FF5555', '#0000FF', '#FFAA00', '#000000'])

        nchannels = kwargs.get("channels", 4)
        self.channels = []
        for i in range(nchannels):
            self.channels.append(ScopePlotChannel('None', self.color_pattern[i]))

        warning = kwargs["WARNING"]

        super().__init__(widget, model, parameters, warning, channels=self.channels, **kwargs)

        #auto-set buffer size to waveform length.  This will be
        #disabled if buffer is set manually
        self.auto_buffer_size = self._win.graphicsWidget.max_length is None
        self.model.status_callback = self.connection_changed
        self.connection_timer = pyqtgraph.QtCore.QTimer()
        self.connection_timer.timeout.connect(self.__check_connection)
        class FlagSignal(QtCore.QObject):
            sig = QtCore.pyqtSignal(bool)
            def __init__(self):
                QtCore.QObject.__init__(self)

        self.connection_timer_signal = FlagSignal()
        self.connection_timer_signal.sig.connect(self.__failed_connection_callback)
        self.buffer_unit = 'Samples'
        self.object_size = None
        self.object_size_tally = []
        
    def __flatten_dict(dobj, kprefixs=[]):
        """
        Genenerator that can traverse through nested dictionaries and return
        key/value pairs

        For example given {'a':{'b':1}, 'c': 2}, it would yield
        ('a.b', 1) and ('c', 2)

        :param dobj dictionary object
        :param kprefixs  list of key of the directary and it's predecessors
        :yields key, value
        """
        sep = '.'
        for k, v in dobj.items():
            if type(v) == dict:
                yield from ScopeController.__flatten_dict(v, kprefixs + [k])
            else:
                yield sep.join(kprefixs + [k]), v

    def get_fdr(self):
        """
        Get EPICS7 PV field description back as a list

        :return: list of field description
        :raise PvaException: raise pvaccess exception when channel cannot be connected.
        """
        fdr = []
        fdr_scalar = []
        pv = self.model.get()
        
        if pv is None:
            return fdr, fdr_scalar

        pv_structure = pv.getStructureDict()
        pv_dictionary = {k:v for k,v in ScopeController.__flatten_dict(pv_structure)}
        for k, v in pv_dictionary.items():
            if type(v) == list and all(type(e) == pva.ScalarType for e in v):
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

    def update_fdr(self, empty=False):
        """
        Update EPICS7 PV field description

        :return:
        """
        if empty:
            fdr = []
            fdr_scalar = []
        else:
            try:
                fdr, fdr_scalar = self.get_fdr()
            except pva.PvaException as e:
                self.notify_warning('Failed to get PV field description: ' + (str(e)))
                return

        fdr.insert(0, "None")
        fdr_scalar.insert(0, "None")

        # fill up the selectable pull down menu for array ID
        child = self.parameters.child("Config").child("ArrayId")
        child.setLimits(fdr_scalar)
        # fill up the selectable pull down menu for x axes
        child = self.parameters.child("Config").child("X Axes")
        child.setLimits(fdr)

        child = self.parameters.child("Trigger").child("Data Time Field")
        child.setLimits(fdr)
        
        for idx in range(len(self.channels)):
            child = self.parameters.child("Channel %s" % (idx + 1))
            c = child.child("Field")
            c.setLimits(fdr)
            c.setValue("None")

    def __failed_connection_callback(self, flag):
        """
        Called initially with flag=False if failed to connect to PV
        Will start periodically checking the connection.
        Once able to connect successfully, this function is called
        again with flag=True
        """
        if not flag:
            # Start periodically checking connection
            self.connection_timer.start(5000)
        else:
            # Got a connection, so turn off timer
            # and reload the fdr
            restart = self._win.graphicsWidget.plotting_started
            self.connection_timer.stop()
            self.stop_plotting()
            self.update_fdr()
            if restart:
                self.start_plotting()                
            
    def connection_changed(self, state, msg):
        for q in self.parameters.child("Acquisition").children():
            if q.name() == 'PV status':
                q.setValue(state)

        if state == 'Failed to connect':
            self.connection_timer_signal.sig.emit(False)

    def __check_connection(self):
        def success_callback(data):
            self.connection_timer_signal.sig.emit(True)

        self.model.async_get(success_callback=success_callback)

    def set_arrayid(self, value):
        """
        Set current field name for array id
            
        :param value:
        :return:
        """
        if value != self.current_arrayid:
            self.current_arrayid = value
            self._win.graphicsWidget.current_arrayid = value

    def set_xaxes(self, value):
        """
        Set current field name for x axes
            
        :param value:
        :return:
        """
        if value != self.current_xaxes:
            self.current_xaxes = value
            self._win.graphicsWidget.set_xaxes(value)

    def set_major_ticks(self, value):
        self._win.graphicsWidget.set_major_ticks(value)

    def set_minor_ticks(self, value):
        self._win.graphicsWidget.set_minor_ticks(value)
    
    def parameter_change(self, params, changes):
        """

        :param params:
        :param changes:
        :return:
        """
        for param, change, data in changes:
            if change == "value":
                path = self.parameters.childPath(param)
                if path is not None:
                    childName = '.'.join(path)
                else:
                    childName = param.name()

                if childName == "Acquisition.PV":
                    # stop DAQ and update pv info
                    try:
                        self.stop_plotting()
                        self.model.update_device(data, restart=False)
                        if data != "":
                            self.update_fdr()
                        else:
                            self.update_fdr(empty=True)

                        # Recalculate object size and readjust buffer size
                        # if PV name changed
                        self.auto_buffer_size = True
                        self.object_size_tally = []
                        self.object_size = None
                    except Exception as e:
                        self.notify_warning('Failed to update PV: ' + (str(e)))
                    
                elif childName == "Acquisition.Start":
                    if data:
                        self.start_plotting()
                    else:
                        self.stop_plotting()
                elif "Channel" in childName:
                    # avoid changes caused by Statistic updating
                    for i, chan in enumerate(self.channels):
                        if childName == 'Channel %s.Field' % (i + 1):
                            chan.pvname = data
                        elif childName == 'Channel %s.DC offset' % (i + 1):
                            chan.dc_offset = data
                        elif childName == 'Channel %s.Axis location' % (i + 1):
                            chan.axis_location = data
                    self._win.graphicsWidget.setup_plot(channels=self.channels)
                elif childName == "Config.ArrayId":
                    self.set_arrayid(data)
                elif childName == "Config.X Axes":
                    self.set_xaxes(data)
                elif childName == "Config.Major Ticks":
                    self.set_major_ticks(data)
                elif childName == "Config.Minor Ticks":
                    self.set_minor_ticks(data)
                elif childName == "Acquisition.Buffer Unit":
                    self.set_buffer_unit(data)
                elif 'Acquisition.Buffer' in childName:
                    self.auto_buffer_size = False
                    self.__calc_buffer_size()
                    
        super().parameter_change(params, changes)
        

    def __calc_buffer_size(self):
        #
        # This function will adjust the number of samples to plot
        # based on buffer size, buffer unit, and object size
        # Called whenever one of these settings has changed
        #
        
        if self.buffer_unit == "Objects":
            if self.object_size:
                nobj = self.parameters.child("Acquisition").child("Buffer (Objects)").value()
                nsamples = nobj * self.object_size
                self._win.graphicsWidget.update_buffer(nsamples)
            
    def update_buffer_samples(self, size):
        """
        Sets number of samples in buffer

        :param size  number of samples
        """
        if self.buffer_unit == 'Samples':
            super().update_buffer_samples(size)
            return

        if self.buffer_unit == 'Objects':
            if self.object_size:
                nobj = math.ceil(size / self.object_size)
                self.parameters.child("Acquisition").child("Buffer (Objects)").setValue(nobj)
                self.__calc_buffer_size()
            else:
                self._win.graphicsWidget.update_buffer(size)
        else:
            raise Exception('Unknown buffer unit %s' % (self.buffer_unit))

    def set_buffer_unit(self, name):
        """
        Set units for buffer size.

        :param name buffer unit.  
        """
        if self.buffer_unit == name:
            return

        param = self.parameters.child("Acquisition").child("Buffer (%s)" % (self.buffer_unit))
        newname = "Buffer (%s)" % (name)
        param.setName(newname)        
        self.buffer_unit = name

        #Update buffer size based on current number of samples
        if self._win.graphicsWidget.max_length:
            self.update_buffer_samples(self._win.graphicsWidget.max_length)
        else:
            if self.buffer_unit == "Objects":
                nobj = self.parameters.child("Acquisition").child("Buffer (Objects)").value()
                if nobj == 0:
                    #default to 1 object
                    self.parameters.child("Acquisition").child("Buffer (Objects)").setValue(1)

                self.__calc_buffer_size()

    def set_object_size(self, size):
        """
        Set number of samples per object

        :param size number of samples per object
        """
        if size == self.object_size:
            return
        
        self.object_size = size
        self.__calc_buffer_size()
        
    def monitor_callback(self, data):
        # Calculate object size
        objlen = 0
        for k, v in ScopeController.__flatten_dict(dict(data)):
            try:
                objlen = max(len(v), objlen)
            except:
                pass

        if not self.object_size and objlen > 0:
            self.set_object_size(objlen)

            #Default buffer size to number of samples in an object
            #if buffer size was not explicitly set
            if self.auto_buffer_size:
                self.update_buffer_samples(self.object_size)

        self.object_size_tally.append(objlen)
        self.object_size_tally = self.object_size_tally[-5:]
        
        if not self._win.graphicsWidget.max_length:
            return
            
        def generator():
            yield from ScopeController.__flatten_dict(dict(data))
        self._win.graphicsWidget.data_process(generator)

    def start_plotting(self):
        """

        :return:
        """
        
        # stop a model first anyway to ensure it is clean
        self.model.stop()
        
        # start a new monitor
        self.model.start(self.monitor_callback)
        
        try:                
            super().start_plotting()
            self.parameters.child("Acquisition").child("Start").setValue(1)
        except Exception as e:
            self.parameters.child("Acquisition").child("Start").setValue(0)
            self.notify_warning('Failed to start plotting: ' + str(e))
            
    def stop_plotting(self):
        """

        :return:
        """
        super().stop_plotting()
        self.parameters.child("Acquisition").child("Start").setValue(0)
        # Stop data source
        self.model.stop()

    def update_status(self):
        super().update_status()

        if len(self.object_size_tally) > 0:
            avg_obj_size = statistics.mean(self.object_size_tally)
            self.parameters.child("Statistics").child('Avg Samples/Obj').setValue(avg_obj_size)
            self.set_object_size(math.ceil(avg_obj_size))
