# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""

import pyqtgraph


class ScopeController:

    def __init__(self, widget, modal, parameters, channels=4):
        """

        :param modal:
        :param parameters:
        :param channels:
        """
        self._win = widget
        self.modal = modal
        self.parameters = parameters
        self.channels = channels
        self.chnames = ["None"] * self.channels
        self.data = None
        # refresh frequency: every 100 ms by default
        self.refresh = 100

        self.plotting_started = False
        self.freeze = False

        self.timer = pyqtgraph.QtCore.QTimer()
        self.timer.timeout.connect(self._win.graphicsWidget.update)
        self._win.graphicsWidget.set_modal(self.modal)

        self.default_arrayid = "None"
        self.default_xaxes = "None"
        self.current_arrayid = "None"
        self.current_xaxes = "None"

    def default_config(self, **kargs):
        """
        Default configuration for array ID and x axes field names

        :param kargs:
        :return:
        """
        self.default_arrayid = kargs.get("arrayid", "None")
        self.default_xaxes = kargs.get("xaxes", "None")
        self.set_xaxes(self.default_xaxes)

    def update_fdr(self, empty=False):
        """
        Update EPICS7 PV field description

        :return:
        """
        if empty:
            fdr = []
            fdr_scalar = []
        else:
            fdr, fdr_scalar = self.modal.get_fdr()
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
                    self.modal.update_pv(data, restart=False)
                    if data != "":
                        self.update_fdr()
                    else:
                        self.update_fdr(empty=True)
                elif childName == "Acquisition.TrigPV":
                    if "://" in data:
                        # pv comes with format of proto://pvname
                        p, name = data.split("://")
                        self.modal.update_trigger(name, proto=p.lower())
                    else:
                        # PV name only, use default pvAccess protocol
                        self.modal.update_trigger(name)
                elif childName == "Acquisition.TriggerMode":
                    self.set_trigger_mode(data)
                elif childName == "Acquisition.PostTrigger":
                    self.set_post_tigger(data)
                elif childName == "Acquisition.HoldTrigger":
                    self.set_hold_trigger(data)
                # elif childName == "Acquisition.Freeze":
                #     self.freeze(data)
                elif childName == "Acquisition.Buffer (Samples)":
                    self._win.graphicsWidget.update_buffer(data)
                elif childName == "Acquisition.Start":
                    self.plotting_started = data
                    if data:
                        self.start_plotting()
                    else:
                        self.stop_plotting()
                elif childName == "Display.Mode":
                    self.set_display_mode(data)
                elif childName == "Display.N Ave":
                    self.set_average(data)
                elif childName == "Display.Autoscale":
                    self._win.graphicsWidget.do_autoscale(data)
                elif childName == "Display.Histogram":
                    self.set_histogram(data)
                elif childName == "Display.Num Bins":
                    self.set_binning(data)
                elif childName == "Display.Refresh":
                    self.set_freshrate(data)
                elif childName == "Config.ArrayId":
                    self.set_arrayid(data)
                elif childName == "Config.X Axes":
                    self.set_xaxes(data)
                else:
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
        self.refresh = value*1000.0
        self.stop_plotting()
        if self.plotting_started:
            self.start_plotting()

    def start_plotting(self):
        """

        :return:
        """
        self.modal.start(self._win.graphicsWidget.data_process)
        self.timer.start(self.refresh)

    def stop_plotting(self):
        """

        :return:
        """
        # Stop timer
        self.timer.stop()
        # Stop data source
        self.modal.stop()

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

    # def freeze(self, flag):
    #     """
    #     Freeze taking data from EPICS7 PV
    #
    #     :param flag:
    #     :return:
    #     """
    #     self.freeze = flag
    #     if self.isplotting:
    #         self.stop_plotting()

    def set_display_mode(self, value):
        """

        :param value:
        :return:
        """

    def set_average(self, value):
        """
        Set average number

        :param value:
        :return:
        """

    def set_autoscale(self, flag):
        """
        Set flag to auto scale plotting

        :param flag:
        :return:
        """

    def set_histogram(self, flag):
        """
        Set flag to enable/disable histogram plotting

        :param flag:
        :return:
        """

    def set_binning(self, value):
        """
        Set number for binning

        :param value:
        :return:
        """
