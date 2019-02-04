# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities for image display

@author: Guobao Shen <gshen@anl.gov>
"""

import pyqtgraph
import pyqtgraph.ptime as ptime
import numpy as np


class PlotWidget(pyqtgraph.GraphicsWindow):
    def __init__(self, parent=None, **kargs):
        pyqtgraph.GraphicsWindow.__init__(self, parent=parent)
        self.setParent(parent)
        self.color_pattern = kargs.get("color",
                                       ['#FFFF00', '#FF00FF', '#55FF55', '#00FFFF', '#5555FF',
                                        '#5500FF', '#FF5555', '#0000FF', '#FFAA00', '#000000'])

        self.param_changed = False
        self.model = None
        self.names = []
        self.auto_scale = False
        self.first_data = True

        # Plotting type:
        #   2: single axes with linear scale
        #   3: single axes with log scale
        #   4: multiple axes with linear scale
        self.plot_type = 2

        # self.axes = None
        self.curve = []
        self.num_axes = 0
        self.plot = self.addPlot()
        # auto range is disabled by default
        self.plot.disableAutoRange()

        self.mutex = pyqtgraph.QtCore.QMutex()

        self.max_length = 256
        self.data_size = 0
        self.new_buffer = True
        self.data = {}
        self.first_run = True

        # last id number of array received
        self.lastArrayId = None
        # count of lost arrays
        self.lostArrays = 0
        # count of array received
        self.arraysReceived = 0

        # EPICS7 field name for horizontal axis
        self.current_xaxes = "None"
        # EPICS7 field name for Array ID
        self.current_arrayid = "None"

        self.fps = None
        self.lastTime = ptime.time()

        self._max = None
        self._min = None

        self.bins = 100
        self.fft = False
        self.psd = False
        self.diff = False
        self.xy = False
        self.histogram = False

    def set_model(self, model):
        """

        :param model:
        :return:
        """
        self.model = model

    def delete_plots(self):
        """
        Delete all plots

        :return:
        """
        if self.curve:
            # if self.plot_type == 2:
            for nn in range(0, len(self.curve)):
                self.plot.removeItem(self.curve[nn])

        self.curve.clear()
        # self.num_axes = 0

    def set_arrayid(self, value):
        """
        Set current field name for array id

        :param value:
        :return:
        """
        if value != self.current_arrayid:
            self.current_arrayid = value

    def set_xaxes(self, value):
        """
        Set current field name for x axes

        :param value:
        :return:
        """
        if value != self.current_xaxes:
            self.current_xaxes = value

    def setup_plot(self, names, single_axis=False, is_log=False):
        """
        Setup plotting

        :param names: list of EPICS7 field names
        :param single_axis: flag to share single axis, or have a axis for each figure
        :param is_log: flag to plot with logarithm for vertical axis
        :return:
        """
        if is_log and not single_axis:
            raise RuntimeError("log is not supported with multi axis")

        counts = len(names)
        self.names = names
        if single_axis:
            # all plotting share single vertical axis
            # the plotting type is 2
            # self.plot_type = 2

            if counts > 0:
                self.delete_plots()

            # TODO support logarithm vertical axes
            # if self.is_log:
            #     self.views[0].setLogMode(True, True)
            # self.axes = self.plot.getAxis('left')
            self.plot.showGrid(x=True, y=True)
            for i in range(counts):
                if names[i] != "None":
                    self.curve.append(self.plot.plot(pen=self.color_pattern[i]))
        else:
            # TODO support multiple axises
            pass

    def do_autoscale(self, flag):
        """

        :param flag:
        :return:
        """
        self.auto_scale = flag
        if flag:
            self.plot.enableAutoRange()
        else:
            self.plot.disableAutoRange()

    def wait(self):
        """

        :return:
        """
        self.mutex.lock()

    def signal(self):
        """

        :return:
        """
        self.mutex.unlock()

    def update_buffer(self, value):
        """

        :param value:
        :return:
        """
        self.max_length = value
        self.new_buffer = True

    def set_range(self, **kwargs):
        """
        Set data range for data filtering.
        Any data out of range will be filtered out, and not plotted.

        :param kwargs:
        :return:
        """
        self._max = kwargs.get("max", None)
        self._min = kwargs.get("min", None)

    def filter(self, data, pair=None):
        """
        Filter data out of range

        :param data:
        :param pair:
        :return:
        """
        rd, rt = data, pair
        if self._max is not None:
            mask = rd <= self._max
            rd = rd[mask]
            if pair is not None:
                rt = rt[mask]
        if self._min is not None:
            mask = rd >= self._min
            rd = rd[mask]
            if pair is not None:
                rt = rt[mask]
        if pair is not None:
            return rd, rt
        return rd

    def set_display_mode(self, value):
        """

        :param value:
        :return:
        """
        if value == 'normal':
            self.fft = False
            self.psd = False
            self.diff = False
            self.xy = False
            self.plot.setLogMode(x=False, y=False)
        elif value == 'fft':
            self.fft = True
            self.psd = False
            self.diff = False
            self.xy = False
            self.plot.setLogMode(x=True, y=True)
        elif value == 'psd':
            self.fft = False
            self.psd = True
            self.diff = False
            self.xy = False
            self.plot.setLogMode(x=True, y=True)
        elif value == 'diff':
            self.fft = False
            self.psd = False
            self.diff = True
            self.xy = False
            self.plot.setLogMode(x=False, y=False)
        elif value == 'xy':
            self.fft = False
            self.psd = False
            self.diff = False
            self.xy = True
            self.plot.setLogMode(x=False, y=False)
        self.plot.autoScale = True

    def set_average(self, value):
        """
        Set average number

        :param value:
        :return:
        """

    def set_histogram(self, flag):
        """
        Set flag to enable/disable histogram plotting

        :param flag:
        :return:
        """
        self.histogram = flag
        self.auto_scale = True

    def set_binning(self, value):
        """
        Set number for binning

        :param value:
        :return:
        """
        self.bins = value
        self.auto_scale = True

    def data_process(self, data):
        """
        Process raw data off the wire

        :param data: raw data right after off the wire thru EPICS7 pvAccess
        :return:
        """
        self.wait()
        newSize = self.data_size

        # start at -1 so we inc to 0 at beginning of loop
        signalcount = -1
        # the first np array is the one we determine trigger position in the data. so as we step all data vectors
        # with k, the 1st vector we mark as "my_trigger_vector"
        my_trigger_vector = -1

        for k, v in data.get().items():
            if k == self.current_arrayid:
                if self.lastArrayId is not None:
                    if v - self.lastArrayId > 1:
                        self.lostArrays += 1
                self.lastArrayId = v
                if self.data_size == 0:
                    newSize += 4
            # when program is here, the v4 field is either a np array, or some sort of scaler.
            # if not an array then we have a scalar, so store the scaler into the local copy of data,
            # and do NOT add to a long stored buffer
            if type(v) != np.ndarray:
                self.data[k] = v
            else:
                # at this point in program we found an nd array that may or may not have data. nd array is
                # not a mark rivers NDArray, but a numpy ndarray.
                # if no data in aa pv field, we just skip this whole loop iteration.
                if len(v) == 0:
                    continue

                # if we get here, then we found an epics array in the v4 pv that has data.
                # we cound array type signals that have data, so triggering works.
                signalcount += 1
                # the 1st time we get here, we actually found k pointing to a data vector,
                # so mark the index of the signal
                if my_trigger_vector == -1:
                    my_trigger_vector = signalcount

                self.data[k] = np.append(self.data.get(k, []), v)[-self.max_length:]

                if self.data_size == 0:
                    if self.data[k][0].dtype == 'float32':
                        newSize += 4 * len(data[k])
                    elif self.data[k][0].dtype == 'float64':
                        newSize += 8 * len(data[k])
                    elif self.data[k][0].dtype == 'int16':
                        newSize += 2 * len(data[k])
                    elif self.data[k][0].dtype == 'int32':
                        newSize += 4 * len(data[k])

        # TODO add trigger support

        self.signal()
        if self.data_size == 0:
            self.data_size = newSize

        self.arraysReceived += 1
        if self.first_data:
            self.first_data = False

    def draw_curve(self, index, data):
        """
        Draw a waveform curve

        :param index:
        :param data:
        :return:
        """

        data_len = len(data)
        # in case on time reference in PV, we declare T to sec per sample.
        # sample period
        sample_period = 1.0
        # time array
        time_array = None

        if self.current_xaxes != "None" and len(self.data[self.current_xaxes]) == data_len:
            # TODO later to support: frequency field & sample period as time reference
            # Currently, support time only
            sample_period = np.diff(self.data[self.current_xaxes]).mean()
            time_array = np.arange(len(data)) * sample_period
        else:
            # TODO need to handle multiple waveform plotting with different data length
            pass

        if self.diff:
            d = np.diff(data)

        if self.fft or self.psd:
            if data_len == 0:
                return
            yf = np.fft.rfft(data)
            xf = np.fft.rfftfreq(data_len, d=sample_period)

        if self.histogram and not self.psd and not self.fft:
            self.curve[index].opts['stepMode'] = True
        else:
            self.curve[index].opts['stepMode'] = False

        if self.fft:
            self.curve[index].setData(xf, (2. / sample_period) * np.abs(yf))
        elif self.psd:
            df = np.diff(xf).mean()
            psd = ((2.0 / sample_period * np.abs(yf)) ** 2) / df / 2
            self.curve[index].setData(xf, psd)
        elif self.histogram and not self.psd and not self.fft:
            d = self.filter(data)
            y, x = np.histogram(d, bins=self.bins)
            self.curve[index].setData(x, y)
        elif time_array is None:
            self.curve[index].setData(self.filter(data))
        else:
            d, t = self.filter(d, time_array)
            self.curve[index].setData(t-t[0], d)

            # TODO support trigger mode
            # if self.trigger_mode and self.is_triggered and is_drawtrigmark:
            #     marktime = self.trigger_timestamp-firsttime
            #     marklinex = np.array([marktime, marktime])
            #     markliney = np.array([1.2 * max(d), 0.8 * min(d)])
            #     self.trigMarker.setData(marklinex, markliney)
            # else:
            #     self.trigMarker.clear()

        if self.first_run or self.new_buffer:
            # perform auto range for the first time
            self.plot.enableAutoRange()
            # then disable it if auto scale is off
            if not self.auto_scale:
                self.plot.disableAutoRange()
            if self.first_run:
                self.first_run = False
            elif self.new_buffer:
                self.new_buffer = False

    def update(self):
        """
        Update display plotting

        :return:
        """
        self.wait()

        if self.first_data:
            # TODO this is to help to over come race condition. To be done in a better way later
            self.signal()
            return

        count = 0
        for name in self.names:
            if name != "None":
                try:
                    data = self.data[name]
                    if data is None:
                        continue
                    self.draw_curve(count, data)
                    count = count + 1
                except KeyError:
                    # TODO solve the race condition in a better way, and add logging support later
                    # data is not ready yet
                    pass

        self.update_fps()
        self.signal()

    def update_fps(self):
        """
        Update fps statistics

        :return:
        """
        now = ptime.time()
        dt = now - self.lastTime
        self.lastTime = now
        if self.fps is None:
            self.fps = 1.0 / dt
        else:
            s = np.clip(dt * 3., 0, 1)
            self.fps = self.fps * (1 - s) + (1.0 / dt) * s

