# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""

import pyqtgraph
import numpy as np


class ScopeController:

    def __init__(self, widget, model, parameters, channels=4):
        """

        :param model:
        :param parameters:
        :param channels:
        """
        self._win = widget
        self.model = model
        self.parameters = parameters
        self.channels = channels
        self.chnames = ["None"] * self.channels
        self.data = None
        # refresh frequency: every 100 ms by default
        self.refresh = 100

        self.plotting_started = False
        self.freeze = False

        self.timer = pyqtgraph.QtCore.QTimer()
        self.timer.timeout.connect(self._win.graphicsWidget.update_drawing)
        self._win.graphicsWidget.set_model(self.model)

        # timer to update status with statistics data
        self.status_timer = pyqtgraph.QtCore.QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

        self.arrays = np.array([])
        self.lastArrays = 0

        self.default_arrayid = "None"
        self.default_xaxes = "None"
        self.current_arrayid = "None"
        self.current_xaxes = "None"

    def default_config(self, **kwargs):
        """
        Default configuration for array ID and x axes field names

        :param kwargs:
        :return:
        """
        arrayid = kwargs.get("arrayid", "None")
        if arrayid is None:
            self.default_arrayid = "None"
        self.set_arrayid(self.default_arrayid)
        xaxes = kwargs.get("xaxes", "None")
        if xaxes is None:
            self.default_xaxes = "None"
        self.set_xaxes(self.default_xaxes)
        self._win.graphicsWidget.set_range(**kwargs)

        self._win.graphicsWidget.max_length = self.parameters.child("Acquisition").child("Buffer (Samples)").value()
        self._win.graphicsWidget.set_binning(self.parameters.child("Display").child("Num Bins").value())

    def update_fdr(self, empty=False):
        """
        Update EPICS7 PV field description

        :return:
        """
        if empty:
            fdr = []
            fdr_scalar = []
        else:
            fdr, fdr_scalar = self.model.get_fdr()
        fdr.insert(0, "None")
        fdr_scalar.insert(0, "None")

        # fill up the selectable pull down menu for array ID
        child = self.parameters.child("Config").child("ArrayId")
        child.setLimits(fdr_scalar)
        # fill up the selectable pull down menu for x axes
        child = self.parameters.child("Config").child("X Axes")
        child.setLimits(fdr)

        for idx in range(self.channels):
            child = self.parameters.child("Channel %s" % (idx + 1))
            c = child.child("Field")
            c.setLimits(fdr)
            c.setValue("None")

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
                    self.model.update_pv(data, restart=False)
                    if data != "":
                        self.update_fdr()
                    else:
                        self.update_fdr(empty=True)
                elif childName == "Acquisition.TrigPV":
                    if "://" in data:
                        # pv comes with format of proto://pvname
                        p, name = data.split("://")
                        self.model.update_trigger(name, proto=p.lower())
                    else:
                        # PV name only, use default pvAccess protocol
                        self.model.update_trigger(name)
                elif childName == "Acquisition.TriggerMode":
                    self.set_trigger_mode(data)
                elif childName == "Acquisition.PostTrigger":
                    self.set_post_tigger(data)
                elif childName == "Acquisition.HoldTrigger":
                    self.set_hold_trigger(data)
                elif childName == "Acquisition.Buffer (Samples)":
                    self._win.graphicsWidget.update_buffer(data)
                elif childName == "Acquisition.Start":
                    # self.plotting_started = data
                    self._win.graphicsWidget.plotting_started = data
                    if data:
                        self.start_plotting()
                    else:
                        self.stop_plotting()
                elif childName == "Display.Mode":
                    self._win.graphicsWidget.set_display_mode(data)
                elif childName == "Display.N Ave":
                    self._win.graphicsWidget.set_average(data)
                elif childName == "Display.Autoscale":
                    self._win.graphicsWidget.do_autoscale(data)
                elif childName == "Display.Histogram":
                    self._win.graphicsWidget.set_histogram(data)
                elif childName == "Display.Num Bins":
                    self._win.graphicsWidget.set_binning(data)
                elif childName == "Display.Refresh":
                    self.set_freshrate(data)
                elif childName == "Config.ArrayId":
                    self.set_arrayid(data)
                elif childName == "Config.X Axes":
                    self.set_xaxes(data)
                elif "Channel" in childName:
                    # avoid changes caused by Statistic updating
                    for i in range(self.channels):
                        if childName == 'Channel %s.Field' % (i + 1):
                            self.chnames[i] = self.parameters.child(path[0]).child('Field').value()
                    self._win.graphicsWidget.setup_plot(self.chnames, single_axis=True)

    def set_freshrate(self, value):
        """
        Set time to refresh

        :param value: time interval to plot, in second
        :return:
        """
        self.stop_plotting()
        self.refresh = value*1000.0
        # if self.plotting_started:
        if self._win.graphicsWidget.plotting_started:
            self.start_plotting()

    def start_plotting(self):
        """

        :return:
        """
        self.model.start(self._win.graphicsWidget.data_process)
        self.timer.start(self.refresh)

    def stop_plotting(self):
        """

        :return:
        """
        # Stop timer
        self.timer.stop()
        # Stop data source
        self.model.stop()

    def set_arrayid(self, value):
        """
        Set current field name for array id

        :param value:
        :return:
        """
        if value != self.current_arrayid:
            self.current_arrayid = value
            self._win.graphicsWidget.set_arrayid(self.current_arrayid)

    def set_xaxes(self, value):
        """
        Set current field name for x axes

        :param value:
        :return:
        """
        if value != self.current_xaxes:
            self.current_xaxes = value
            self._win.graphicsWidget.set_xaxes(self.current_xaxes)

    def set_trigger_mode(self, value):
        """

        :param value:
        :return:
        """

    def set_post_trigger(self, value):
        """
        Set the time period after the trigger.

        :param value:
        :return:
        """
        # TODO need to understand this requirement more to implement it
        # it is currently a place holder

    def set_hold_trigger(self, value):
        """
        Set time period to hold the trigger

        :param value:
        :return:
        """
        # TODO need to understand this requirement more to implement it
        # it is currently a place holder

    def update_status(self):
        """
        Update statistics status.

        :return:
        """
        with self._win._proc.oneshot():
            cpu = self._win._proc.cpu_percent(None)

        # TODO algorithm to calculate Array/sec
        arraysReceived = self._win.graphicsWidget.arraysReceived
        n = arraysReceived - self.lastArrays
        self.lastArrays = arraysReceived
        self.arrays = np.append(self.arrays, n)[-10:]

        for q in self.parameters.child("Statistics").children():

            if q.name() == 'CPU':
                q.setValue(cpu)
            elif q.name() == 'Lost Arrays':
                q.setValue(self._win.graphicsWidget.lostArrays)
            elif q.name() == 'Tot. Arrays':
                q.setValue(self._win.graphicsWidget.arraysReceived)
            elif q.name() == 'Arrays/Sec':
                q.setValue(self.arrays.mean())
            elif q.name() == 'Bytes/Sec':
                q.setValue(self.arrays.mean() * self._win.graphicsWidget.data_size)
            elif q.name() == 'Rate':
                q.setValue(self._win.graphicsWidget.fps)
            elif q.name() == 'TrigStatus':
                stat_str = "Not Trig Mode,Not Monitoring"
                # if self.pvaChannel.trigger_is_monitor:
                #     stat_str = "Not Trig Mode, Monitoring TrigPV"
                #     if self.pvaChannel.trigger_mode:
                #         stat_str = "Waiting for Trigger, Collecting"
                #         if self.pvaChannel.is_triggered:
                #             stat_str = "Got Trigger, Collecting"
                #             if self.pvaChannel.trigger_data_done:
                #                 stat_str = "Got Trigger, Done Collecting"
                q.setValue(stat_str)
