# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

"""

import numpy as np
import pyqtgraph as pg


class UiManage:
    """

    """
    def __init__(self, channel, parameters, args, plots=[]):
        """

        :param channel: EPICS pvAccess Channel
        """
        self.pvaChannel = channel
        self.statistics = {
            'arrays': np.array([]),
            'bytes': np.array([]),
            'lastArrays': 0
        }
        self.parameters = parameters
        self.params = args
        self.plots = plots

    def updateUI(self):
        n = self.pvaChannel.arraysReceived - self.statistics['lastArrays']
        self.statistics['lastArrays'] = self.pvaChannel.arraysReceived
        self.statistics['arrays'] = np.append(self.statistics['arrays'], n)[-10:]
        for p in self.parameters.children():
            if p.name() == 'Statistics':
                for q in p.children():
                    if q.name() == 'Lost Arrays':
                        q.setValue(self.pvaChannel.lostArrays)
                    elif q.name() == 'Tot. Arrays':
                        q.setValue(self.pvaChannel.arraysReceived)
                    elif q.name() == 'Arrays/Sec':
                        q.setValue(self.statistics['arrays'].mean())
                    elif q.name() == 'Bytes/Sec':
                        q.setValue(self.statistics['arrays'].mean() * self.pvaChannel.size)
                    elif q.name() == 'Refresh':
                        q.setValue(self.plots[0].fps)
                    elif q.name() == 'TrigStatus':
                        stat_str = "Not Trig Mode,Not Monitoring"
                        if self.pvaChannel.trigger_is_monitor:
                            stat_str = "Not Trig Mode, Monitoring TrigPV"
                            if self.pvaChannel.trigger_mode:
                                stat_str = "Waiting for Trigger, Collecting"
                        q.setValue(stat_str)

    def paramChange(self, param, changes):
        if not self.plots:
            return

        for param, change, data in changes:
            path = self.parameters.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
            # print ('  parameter: %s' % childName)
            # print ('  change:    %s' % change)
            # print ('  data:      %s' % str(data))
            # print ('-------------')
            if childName == 'Acquisition.Buffer':
                self.pvaChannel.maxlen = data
                self.plots[0].autoScale = True
                self.plots[0].param_changed = True
            elif childName == 'Acquisition.TrigPV':
                self.params["TRIGGER"]["PV"] = data
                # if alreade conn to a pv, disconnect
                self.pvaChannel.stopTriggerPVMode(True)
            elif childName == 'Acquisition.WaitTrigger':
                self.params["IS_WAITTRIG"] = data
                if data is True:
                    self.pvaChannel.startTriggerPVMode(self.params["TRIGGER"]["PV"],
                                                       self.pvaChannel.maxlen / 2)
                    self.plots[0].setTrigMode('ext')
                else:
                    self.pvaChannel.stopTriggerPVMode()
                    if self.params["IS)FREEZE"]:
                        self.plots[0].setTrigMode('single')
                    else:
                        self.plots[0].setTrigMode('auto')
            elif childName == 'Acquisition.Freeze':
                self.params["IS_FREEZE"] = data
                if data:
                    self.plots[0].setTrigMode('single')
                elif self.pvaChannel.trigger_mode:
                    self.plots[0].setTrigMode('ext')
                else:
                    self.plots[0].setTrigMode('auto')
            elif childName == 'Display.Mode':
                self.plots[0].param_changed = True
                if data == 'normal':
                    self.params["ALGORITHM"] = "NORMAL"
                    # self.args.fft = False
                    # self.args.psd = False
                    # self.args.diff = False
                    # self.args.x_vs_y = False
                elif data == 'fft':
                    self.params["ALGORITHM"] = "FFT"
                    # self.args.fft = True
                    # self.args.psd = False
                    # self.args.diff = False
                    # self.args.x_vs_y = False
                elif data == 'psd':
                    self.params["ALGORITHM"] = "PSD"
                    # self.args.fft = False
                    # self.args.psd = True
                    # self.args.diff = False
                    # self.args.x_vs_y = False
                elif data == 'diff':
                    self.params["ALGORITHM"] = "DIFF"
                    # self.args.fft = False
                    # self.args.psd = False
                    # self.args.diff = True
                    # self.args.x_vs_y = False
                elif data == 'x_vs_y':
                    self.params["ALGORITHM"] = "XvsY"
                    # self.args.fft = False
                    # self.args.psd = False
                    # self.args.diff = False
                    # self.args.x_vs_y = True
                self.plots[0].autoScale = True
            elif childName == 'Display.Autoscale':
                self.plots[0].lockAutoscale = data
            elif childName == 'Display.Histogram':
                self.params["HISTOGRAM"] = data
                self.plots[0].autoScale = True
            elif childName == 'Display.Num Bins':
                self.params["N_BINS"] = data
                self.plots[0].autoScale = True
            elif childName == 'Display.Refresh':
                self.plots[0].timer.setInterval(data * 1000)

            for i in range(0, self.params["N_CHANNELS"]):
                if childName == 'Channel %s.Field' % (i + 1):
                    self.plots[0].param_changed = True
                    # fieldName = self.fieldNameMap.get(data, data)
                    fieldName = self.params["FIELD_NAMES"].get(data, data)
                    self.plots[0].setFieldName(i, fieldName)
                    self.plots[0].autoScale = True

    def setWindowTitle(self, title):
        self.win.setWindowTitle(title)

    def setPlotAntialias(self, antialias):
        pg.setConfigOptions(antialias=antialias)

