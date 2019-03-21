# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities for image display

@author: Guobao Shen <gshen@anl.gov>
"""

import numpy as np
import pyqtgraph
import pyqtgraph.ptime as ptime
from pyqtgraph.Qt import QtCore


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
        self.plotting_started = False

        # Plotting type:
        #   2: single axes with linear scale
        #   3: single axes with log scale
        #   4: multiple axes with linear scale
        # self.plot_type = 2

        # self.axes = None
        self.curve = []
        self.num_axes = 0
        self.plot = self.addPlot()
        # auto range is disabled by default
        self.plot.disableAutoRange()
        # trigger marker
        self.trigMarker = self.plot.plot(pen='r')

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

        self.dc_offsets = None

        ##############################
        #
        # trigger related variables
        #
        ##############################
        # num samples to take after trigger
        self.samples_after_trig = 0
        # number of sample captured after trigger
        self.samples_after_trig_cnt = 0

        # self.trigger_buffer_position = 0
        # self.samples_before_trig = 0

        self.trigger_mode = False
        self.trigger_data_done = True
        # true if in trig mode and trig was received. that is the pv mon fired.
        self.is_triggered = False
        # counts whenever trigger pv monitor fires callback
        self.trigger_count = 0
        # true of we are monitoring a channel
        self.trigger_is_monitor = False
        # true if we put in bad pv name, and try to monitor
        self.trigger_pv_error = False
        # double sec past epoch timestamp from the trig pv
        self.trigger_timestamp = 0.0

        self.trigger_rec_type = None
        self.trigger_level = 0.0
        ##############################
        #
        # End Trigger mode variables
        #
        ##############################

        self.is_freeze = False

        class Foo(QtCore.QObject):
            my_signal = QtCore.pyqtSignal()

            def __init__(self):
                QtCore.QObject.__init__(self)

        self.plot_signal_emitter = Foo()

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
            for nn in range(0, len(self.curve)):
                self.plot.removeItem(self.curve[nn])

        self.curve.clear()

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
        self.samples_after_trig = int(self.max_length/2)
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

    def trigger_process(self, data):
        """
        Process trigger signal. It currently supports EPICS classic record types,
        which are ai/ao, bi/bo, calc, longin/longout, and event.

        It generates a trigger event when it receives an EPICS event and the previous trigger process is done.

        For a bi/bo type trigger, the trigger event is generated at rising edge, which means 0 => 1, and ignores
        the event 1 => 0.

        For a longin/longout type trigger, it always generates a trigger when there is any value change,
        and previous trigger is done.

        For event and calc type trigger, it behaviors the same with longin/longout.

        For a ai/ao type trigger, it generates a trigger event when
            1. its value is greater than give threshold;
            2. previous trigger is done;
            3. triggering at rising edge;
        It will be triggered again once the current plotting is done even for the same trigger edge.
        A special approach shall be adopted to handle the trigger event caused by the same rising edge.

        More algorithm to be added later when needed.
        The current implementation is the first approach, and shall be reconsidered when needed.

        :param data:
        :return:
        """
        # TODO handle trigger event for the case of plotting freezing,
        # need to handle multiple trigger before done with current trigger, and during plotting freezing
        #
        if self.trigger_data_done:
            # only accept new trigger after the current trigger done
            if self.trigger_rec_type in ["bi", "bo"]:
                # only trigger during jumping from 0 => 1
                if data["value"]["index"] == 1:
                    self.is_triggered = True
                    self.trigger_data_done = False
            elif self.trigger_rec_type in ["longin", "longout"]:
                # always triggers when values changes
                self.is_triggered = True
                self.trigger_data_done = False
            elif self.trigger_rec_type in ["calc"]:
                # always triggers when values changes
                self.is_triggered = True
                self.trigger_data_done = False
            elif self.trigger_rec_type in ["event"]:
                # always triggers when values changes
                # TODO compare the time stamp to determine the event trigger
                self.is_triggered = True
                self.trigger_data_done = False
            elif self.trigger_rec_type in ["ai", "ao"]:
                # always triggers when values changes
                if data["value"] >= self.trigger_level:
                    self.is_triggered = True
                    self.trigger_data_done = False
                else:
                    self.is_triggered = False

            self.trigger_count = self.trigger_count + 1
            ts = data['timeStamp']
            # because the callback happens on connection, we set flag on 2nd callback, when monitor fires for real.
            # also, we only call this stuff if is_triggered is False
            # so we don't trigger again before we process the last trigger.
            # also, if hold off ignore, then during a hold off time, we ignore triggers for example for 1 second.
            if self.trigger_count > 0 and self.is_triggered:
                self.samples_after_trig_cnt = 0
                self.trigger_timestamp = ts['secondsPastEpoch'] + 1e-9*ts['nanoseconds']

    def data_process(self, data):
        """
        Process raw data off the wire

        :param data: raw data right after off the wire thru EPICS7 pvAccess
        :return:
        """
        self.wait()
        new_size = self.data_size

        # assume a triggers done then set false when we gather data.
        # all_triggers_done = True
        # we step through all the signals we get from the v4 pv. we keep a count of them
        # start at -1 so we inc to 0 at beginning of loop
        signal_count = -1
        # the first np array is the one we detrmine trigger position in the data. so as we step all data vectors
        # with k, the 1st vector we mark as "vector_data_count"
        vector_data_count = -1

        if not self.is_freeze:
            for k, v in data.get().items():
                if k == self.current_arrayid:
                    if self.lastArrayId is not None:
                        if v - self.lastArrayId > 1:
                            self.lostArrays += 1
                    self.lastArrayId = v
                    if self.data_size == 0:
                        new_size += 4
                if type(v) is list:
                    v = np.array(v)
                # when program is here, the v4 field is either a np array, or some sort of scalar.
                # if not an array then we have a scalar, so store the scalar into the local copy of data,
                # and do NOT add to a long stored buffer
                if type(v) != np.ndarray:
                    self.data[k] = v
                else:
                    # at this point in program we found an nd array that may or may not have data. nd array is
                    # not an EPICS7 NDArray, but a numpy ndarray.
                    # if no data in aa pv field, we just skip this whole loop iteration.
                    if len(v) == 0:
                        continue

                    # if we get here, then we found an epics array in the EPICS7 pv that has data.
                    # count array type signals that have data, so triggering works.
                    signal_count += 1
                    # the 1st time we get here, we actually found k pointing to a data vector,
                    # so mark the index of the signal
                    if vector_data_count == -1:
                        vector_data_count = signal_count

                    vector_len = len(v)

                    self.data[k] = np.append(self.data.get(k, []), v)[-self.max_length:]
                    if self.size == 0:
                        if self.data[k][0].dtype == 'float32':
                            new_size += 4 * len(data[k])
                        elif self.data[k][0].dtype == 'float64':
                            new_size += 8 * len(data[k])
                        elif self.data[k][0].dtype == 'int16':
                            new_size += 2 * len(data[k])
                        elif self.data[k][0].dtype == 'int32':
                            new_size += 4 * len(data[k])

            # if we got a vector of data, then we deal with triggering.
            if vector_data_count != -1 and self.trigger_mode:
                # it means trigger type is either single shot, or run/stop
                if self.is_triggered:
                    self.samples_after_trig_cnt = self.samples_after_trig_cnt + vector_len
                    if self.samples_after_trig_cnt >= self.samples_after_trig:
                        self.plot_signal_emitter.my_signal.emit()
            # else:
            #     # trigger type is "", which means not in trigger mode
            #     self.plot_signal_emitter.my_signal.emit()

        self.signal()
        if self.data_size == 0:
            self.data_size = new_size

        self.arraysReceived += 1
        if self.first_data:
            self.first_data = False

    def draw_curve(self, count, data, index, draw_trig_mark=False):
        """
        Draw a waveform curve

        :param count:  count of curve for plotting
        :param data:   curve data for plotting
        :param index:  DC offset index
        :param draw_trig_mark: flag whether drawing trigger mark
        :return:
        """
        data_len = len(data)
        # in case on time reference in PV, we declare sample period to sec per sample.
        # 1 second per sample as initial
        sample_period = 1.0
        # time array
        time_array = None

        if self.current_xaxes != "None" and len(self.data[self.current_xaxes]) == data_len:
            # TODO later to support: frequency field & sample period as time reference
            # TODO need to handle multiple waveform plotting with different data length
            # Currently, support time only
            sample_period = np.diff(self.data[self.current_xaxes]).mean()
            time_array = self.data[self.current_xaxes]

        if self.diff:
            d = np.diff(data)

        if self.fft or self.psd:
            if data_len == 0:
                return
            yf = np.fft.rfft(data)
            xf = np.fft.rfftfreq(data_len, d=sample_period)

        if self.histogram and not self.psd and not self.fft:
            self.curve[count].opts['stepMode'] = True
        else:
            self.curve[count].opts['stepMode'] = False

        if self.fft:
            self.curve[count].setData(xf, (2. / sample_period) * np.abs(yf))
        elif self.psd:
            df = np.diff(xf).mean()
            psd = ((2.0 / sample_period * np.abs(yf)) ** 2) / df / 2
            self.curve[count].setData(xf, psd)
        elif self.histogram and not self.psd and not self.fft:
            d = self.filter(data)
            y, x = np.histogram(d, bins=self.bins)
            self.curve[count].setData(x, y)
        elif time_array is None:
            self.curve[count].setData(self.filter(data) + self.dc_offsets[index])
            self.__handle_trigger_marker__(draw_trig_mark, self.max_length - self.samples_after_trig_cnt)
        else:
            d, t = self.filter(data, time_array)
            self.curve[count].setData(t - t[0], d + self.dc_offsets[index])
            self.__handle_trigger_marker__(draw_trig_mark, self.trigger_timestamp - time_array[0])

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

    def __handle_trigger_marker__(self, draw_trig_mark, marktime):
        """

        :param draw_trig_mark:
        :param marktime:
        :return:
        """
        if self.trigger_mode and self.is_triggered:
            if draw_trig_mark:
                # Add trigger marker on plotting
                # TODO fix potential risk that Y axes range increasing cause by trigger marker
                self.trigMarker.setData(np.array([marktime, marktime]),
                                        np.array(self.plot.viewRange()[1]) * 0.75)
        else:
            self.trigMarker.clear()

    def update_drawing(self):
        """
        Update display plotting

        :return:
        """
        if self.first_data or not self.plotting_started:
            # TODO this is to help to over come race condition. To be done in a better way later
            # self.signal()
            return

        self.wait()

        count = 0
        draw_trig_mark = True
        for idx, name in enumerate(self.names):
            if name != "None":
                try:
                    data = self.data[name]
                    if data is None:
                        continue
                    self.draw_curve(count, data, idx, draw_trig_mark)
                    draw_trig_mark = False
                    count = count + 1
                except KeyError:
                    # TODO solve the race condition in a better way, and add logging support later
                    # data is not ready yet
                    pass

        if self.trigger_mode and self.is_triggered:
            self.is_triggered = False
            self.trigger_data_done = True

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

