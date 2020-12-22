# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities for image display

@author: Guobao Shen <gshen@anl.gov>
"""
from datetime import datetime
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

        self.mutex = pyqtgraph.QtCore.QMutex()

        self.max_length = 256
        self.data_size = 0
        self.new_buffer = True
        self.data = {}
        self.trig_data = {}
        self.first_run = True
        self.new_plot = True

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

        self.fps = 0
        self.lastTime = ptime.time()

        self._max = None
        self._min = None

        self.bins = 100
        self.fft = False
        self.fft_filter = None
        self.psd = False
        self.diff = False
        self.xy = False
        self.histogram = False
        self.average = 1

        self.__fft_vgain = {
            'none' : 1,
            'hamming' : 1.853,
        }

        self.axis = []
        self.default_axis_location = "left"
        self.axis_locations = {
            0 : self.default_axis_location,
            1 : self.default_axis_location,
            2 : self.default_axis_location,
            3 : self.default_axis_location,
        }
        self.default_dc_offset = 0
        self.dc_offsets = {
            0 : self.default_dc_offset,
            1 : self.default_dc_offset,
            2 : self.default_dc_offset,
            3 : self.default_dc_offset,
        }
        self.views = []
        self.curves = []

        # Setup plot variables
        self.single_axis = True
        self.plot = None
        self.setup_plot([])


        ##############################
        #
        # trigger related variables
        #
        ##############################
        # Is trigger mode enabled
        self.trigger_mode = False

        # True if in trigger mode and trigger was received (trigger PV monitor fired).
        self.is_triggered = False

        # Counts trigger PV monitor fired callback (count monitor updates)
        self.trigger_count = 0

        # Number samples to take after trigger
        self.samples_after_trig = 0

        # Number of samples captured after trigger
        self.samples_after_trig_cnt = 0

        # Buffer managemet
        self.trigger_buffer_position = 0
        self.samples_before_trig = 0

        self.trigger_data_done = True

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

        class TriggerSignal(QtCore.QObject):
            my_signal = QtCore.pyqtSignal()

            def __init__(self):
                QtCore.QObject.__init__(self)

        self.plot_trigger_signal_emitter = TriggerSignal()

    def set_model(self, model):
        """

        :param model:
        :return:
        """
        self.model = model

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

    def setup_plot(self, names, single_axis=True):
        """
        Setup plotting

        :param names: list of EPICS7 field names
        :param single_axis: flag to share single axis, or have a axis for each figure. FFT and PSD support only single axis
        :return:
        """

        # FFT and PSD support only single axis, PyQTGraph currently doesn't support log scale on the multiple axis setup
        if not single_axis and (self.fft or self.psd):
            single_axis = True
            # Could Be replaced with logging if added in the future
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: FFT or PSD selected in multi axis mode, which is not supported. Changed to one axis mode automatically.")

        # Delete existing plots
        self.delete_plots()

        # Set new list of signals
        self.names = names

        # Create plot item
        self.plot = pyqtgraph.PlotItem()
        self.plot.showGrid(x=True, y=True)
        self.trigMarker = self.plot.plot(pen='r')
        self.do_autoscale()
        if self.fft or self.psd:
            self.plot.setLogMode(x=True, y=True)

        # Generate plot items
        self.single_axis = single_axis
        if single_axis:
            self.setup_plot_single_axis(names)
        else:
            self.setup_plot_multi_axis(names)

        # Update plots
        self.plot.vb.sigResized.connect(self.update_views)
        self.update_views()

        # Set for autoscale the first time
        self.new_plot = True

    def setup_plot_single_axis(self, names):
        """
        Setup items for single Y axis plot.

        :names: (list -> strings) List of channels to bi displayed. "None" should be used to ignore that channel.
        :return: (None)
        """
        for i in range(len(names)):
            if names[i] != "None":
                curve = self.plot.plot(pen=self.color_pattern[i])
                curve.plotdata_ave = None
                self.curves.append(curve)

        self.ci.addItem(self.plot, row=2)

    def setup_plot_multi_axis(self, names):
        """
        Setup items for multiple Y axis plot.

        :names: (list -> strings) List of channels to bi displayed. "None" should be used to ignore that channel.
        :return: (None)
        """
        # We do not use default axis
        self.plot.hideAxis('left')

        # Create axis and views
        left_axis = []
        right_axis = []
        for i, field_name in enumerate(names):
            # Skip if None was selected
            if field_name == "None":
                continue
            axis = pyqtgraph.AxisItem(self.axis_locations[i])
            axis.setLabel(f"Channel {i+1} [{field_name}]", color=self.color_pattern[i])
            if self.axis_locations[i] == "left":
                left_axis.append(axis)
            else:
                right_axis.append(axis)
            self.axis.append(axis)
            # First view we take from plotItem
            if len(self.axis) == 1:
                self.views.append(self.plot.vb)
            else:
                self.views.append(pyqtgraph.ViewBox())

        # Add axis and plot to GraphicsLayout (self.ci)
        # Order how they are added is important, while it is also important
        # we hold correct order (the same as in the "names" variable) in self.axis
        # variable as other code depends on this.
        for a in left_axis:
            self.ci.addItem(a, row=2)
        self.ci.addItem(self.plot, row=2)
        for a in right_axis:
            self.ci.addItem(a, row=2)

        # Add Viewboxes to the layout
        for vb in self.views:
            if vb != self.plot.vb:
                self.ci.scene().addItem(vb)

        # Link axis to view boxes
        for i, view in enumerate(self.views):
            self.axis[i].linkToView(view)
            if view != self.plot.vb:
                view.setXLink(self.plot.vb)

        # Make curves
        count = 0
        for i, field_name in enumerate(names):
            if field_name == "None":
                continue
            curve = pyqtgraph.PlotCurveItem(pen=self.color_pattern[i])
            curve.plotdata_ave = None
            left_curve = []
            right_curve = []
            if self.axis_locations[i] == "left":
                left_curve.append(curve)
            else:
                right_curve.append(curve)
            self.curves.extend(left_curve)
            self.curves.extend(right_curve)
            self.views[count].addItem(curve)
            count += 1

    def delete_plots(self):
        """
        Delete all plots

        :return:
        """
        if self.single_axis:
            for curve in self.curves:
                self.plot.removeItem(curve)
        else:
            # Delete old plots if exists
            for i, view in enumerate(self.views):
                view.removeItem(self.curves[i])

            for a in self.axis:
                self.ci.removeItem(a)

        # Remove plotItem
        if self.plot is not None:
            self.ci.removeItem(self.plot)

        # Remove references to all chart items
        self.views = []
        self.axis = []
        self.curves = []

    def update_views(self):
        """
        Update the view so they scale properly.

        :return:
        """
        for view in self.views:
            if view == self.plot.vb:
                continue
            view.setGeometry(self.plot.vb.sceneBoundingRect())

    def set_autoscale(self, flag):
        """
        Enable or disable the autoscale.

        :param flag: (bool) True to enable the autoscale, False otherwise.
        :return:
        """
        self.auto_scale = flag
        self.do_autoscale()


    def do_autoscale(self, auto_scale=None):
        """
        Enable/disable auto range of the current plot based on the `self.auto_scale` setting.

        :param auto_scale: (bool) Can used to overwrite the self.auto_scale. Keep non to use self.auto_scale.
        :return:
        """
        if auto_scale is None:
            auto_scale = self.auto_scale

        if auto_scale:
            self.plot.enableAutoRange()
            for view in self.views:
                view.enableAutoRange()
        else:
            self.plot.disableAutoRange()
            for view in self.views:
                view.disableAutoRange()

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
        elif value == 'fft':
            self.fft = True
            self.psd = False
            self.diff = False
            self.xy = False
        elif value == 'psd':
            self.fft = False
            self.psd = True
            self.diff = False
            self.xy = False
        elif value == 'diff':
            self.fft = False
            self.psd = False
            self.diff = True
            self.xy = False
        elif value == 'xy':
            self.fft = False
            self.psd = False
            self.diff = False
            self.xy = True
        self.plot.autoScale = True

        # Mode changed, iterate over the curves and set moving average to None
        for curve in self.curves:
            curve.plotdata_ave = None

    def set_fft_filter(self, value):
        """
        Set fft filter to use. Valid values are None / "none" and "hamming".

        :param value: (None or string) Filter to be used on the data, before the fft.
        :return:
        """
        if value is None:
            self.fft_filter = value
        else:
            self.fft_filter = value.lower()

    def set_average(self, value):
        """
        Set average number

        :param value:
        :return:
        """
        self.average = value

    def set_histogram(self, flag):
        """
        Set flag to enable/disable histogram plotting

        :param flag:
        :return:
        """
        if flag != self.histogram:
            self.new_plot = True

        self.histogram = flag

    def set_binning(self, value):
        """
        Set number for binning

        :param value:
        :return:
        """
        self.bins = value

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

        # Count triggers and ignore first one which is initial connection callback and not actual value change.
        self.trigger_count += 1
        if self.trigger_count <= 1:
            return

        # Ignore trigger if we are not ploting
        if not self.plotting_started:
            return

        #  We trigger again only if the last trigger was fully processed
        if not self.trigger_data_done:
            return

        # Process callback
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

        # TODO: also, if hold off ignore, then during a hold off time, we ignore triggers for example for 1 second.

        if self.is_triggered:
            self.samples_after_trig_cnt = 0
            ts = data['timeStamp']
            self.trigger_timestamp = ts['secondsPastEpoch'] + 1e-9*ts['nanoseconds']

    def __is_trigger_in_array(self, time_array):
        """
        Calculate if the trigger timestap is in the timestamp array.

        :param time_array: (numpy array) Time (SORTED!!!) array to be checked.
        :return: (Tuple -> (bool, integer)) True or False if timestamp is in the array.
                                            If True, second element hold index of the element, otherwise is None.
        """

        idx = np.searchsorted(time_array, self.trigger_timestamp)

        if idx <= 0 or idx >= time_array.size-1:
            return (False, None)
        else:
            return (True, idx)


    def data_process(self, data_generator):
        """
        Process raw data off the wire

        :param data_generator: generator that yields pvaccess data from the wire as key/value pairs
        :return:
        """
        # Increment array count
        self.arraysReceived += 1

        # Check if scope is frozen
        if self.is_freeze:
            return

        self.wait()
        new_size = self.data_size
        vector_len = 0

        # Assume a triggers done then set false when we gather data.
        # all_triggers_done = True

        # We step through all the signals we get from the v4 pv. We keep a count of them
        # start at -1 so we increment to 0 at beginning of loop.
        signal_count = -1

        # The first np array is the one we determine trigger position in the data. So as we step all data vectors
        # with k, the 1st vector we mark as "vector_data_count".
        vector_data_count = -1


        for k, v in data_generator():

            # TODO: what is this logic doing?
            if k == self.current_arrayid:
                if self.lastArrayId is not None:
                    if v - self.lastArrayId > 1:
                        self.lostArrays += 1
                self.lastArrayId = v
                if self.data_size == 0:
                    new_size += 4

            # If pvaccess modules was build without numpy, normal Python list is returned. Make conversion here.
            if type(v) is list:
                v = np.array(v)

            # When program is here, the v4 field is either a np array, or some sort of scalar.
            if type(v) != np.ndarray:
                # If not an array then we have a scalar, so store the scalar into the local copy of data,
                # and do NOT add to a long stored buffer
                self.data[k] = v

            else:
                # At this point in program we found an nd array that may or may not have data. nd array is
                # not an EPICS7 NDArray, but a numpy ndarray.
                # If no data in a pv field, we just skip this whole loop iteration.
                if len(v) == 0:
                    continue

                # If we get here, then we found an epics array in the EPICS7 pv that has data.
                # Count array type signals that have data, so triggering works.
                signal_count += 1

                # The 1st time we get here, we actually found k pointing to a data vector,
                # so mark the index of the signal
                if vector_data_count == -1:
                    vector_data_count = signal_count

                # Number of elements in vector
                vector_len = len(v)

                # Here we store the data to class variables for later ploting. How much data we must store depends on the
                # mode we are in.
                if self.trigger_mode:
                    # In trigger mode the minimum we must save is the whole last array (+ part of the old ones if max_length > vector_len)
                    # We must store all the arrayes as the "Time" field determinate how much data do we really need, and the "Time" field can arrive last.
                    required_data = 2 * (vector_len if vector_len > self.max_length else self.max_length)
                    self.data[k] = np.append(self.data.get(k, []), v)[-required_data:]
                else:
                    # We are in free running mode. Only last max_length of the data can be stored.
                    self.data[k] = np.append(self.data.get(k, []), v)[-self.max_length:]

                # TODO: This is not used anywhere. What should be used for?
                if self.size == 0:
                    if self.data[k][0].dtype == 'float32':
                        new_size += 4 * len(self.data[k])
                    elif self.data[k][0].dtype == 'float64':
                        new_size += 8 * len(self.data[k])
                    elif self.data[k][0].dtype == 'int16':
                        new_size += 2 * len(self.data[k])
                    elif self.data[k][0].dtype == 'int32':
                        new_size += 4 * len(self.data[k])

        # Trigger mode is enabled, trigger triggered and we received vector data, execute trigger procedure.
        if (self.trigger_mode
            and self.is_triggered
            and vector_data_count != -1):

            # Check if we have trigger timestamp in buffer
            in_array, idx = self.__is_trigger_in_array(self.data['Time'])
            if in_array:
                self.samples_after_trig_cnt = self.data['Time'].size - idx

                # Check if we have the requested number of samples, to trigger the plotting
                if self.samples_after_trig_cnt >= self.samples_after_trig:
                    for k, v in self.data.items():
                        if type(v) != np.ndarray:
                            continue
                        # `idx` holds the index in the stored waveforms where the trigger happened.
                        # Goal is to get the slice of the waveform so the sample when the trigger happened is in the middle.
                        # samples_after_trig determinate how much samples do we want to show after the trigger (idx + samples_after_trig),
                        # while max_length holds a maximum number of samples to show, for this reason we need `(self.max_length-self.samples_after_trig`
                        # samples before trigger/idx.
                        self.trig_data[k] = v[idx-(self.max_length-self.samples_after_trig) : idx+self.samples_after_trig]
                    self.plot_trigger_signal_emitter.my_signal.emit()

        self.signal()
        if self.data_size == 0:
            self.data_size = new_size

        if self.first_data:
            self.first_data = False

    def calculate_ftt(self, data, sample_period, mode, filter=None):
        """
        Calculate fft on the input array.

        :param data: (Numpy array) Data to be transformed.
        :param sample_period: (int) Sampling period of the data.
        :param mode: (string) This could be either "fft" or "psd".
        :param filter: (None or string) Filter to be applied on the data before transformation.

        :return: (Numpy array, Numpy array) xf and yf transformations of the data.
        """
        xf = yf = None
        filter = filter or "none"

        # Perform transformation for X axis
        data_len = len(data)
        xf = np.fft.rfftfreq(data_len, d=sample_period)

        # Calculate window
        if filter == "none":
            pass
        elif filter == "hamming":
            window = np.hamming(data_len)
            data = data * window
        else:
            raise ValueError(f"{str(filter)} is not valid FFT filter type.")

        # Perform transformation for Y axis
        yf_raw = np.abs(np.fft.rfft(data))

        # Apply normalisation filter
        try:
            vertical_gain = self.__fft_vgain[filter]
        except KeyError:
            raise ValueError(f"{str(filter)} is not valid FFT filter type.")

        if mode.lower() == "fft":
            yf = 2. * vertical_gain * yf_raw / data_len
            # DC bin has different scale factor
            yf[0] = yf[0] / 2.
        elif mode.lower() == "psd":
            # Sample period in sec. Sample rate is 1/sample rate. Hz/bin=srage/nf
            sample_rate = 1. / sample_period
            yf = 2. * vertical_gain * vertical_gain * yf_raw * yf_raw / (sample_rate * sample_rate)
            # DC bin has different scale factor
            yf[0] = yf[0] / 4.
        else:
            raise ValueError(f"{str(mode)} is not valid mode for FFT.")

        return xf, yf

    def exponential_moving_average(self, data, data_ave):
        """
        Calculate exponential moving average on the data.

        :param data: (ndarray) Latest array data.
        :param data_ave: (ndarray) Data average until now.

        :return: (ndarray) Exponential moving average.
        """
        alpha = 2. / (self.average + 1.)

        if data_ave is None or len(data_ave) != len(data):
            data_ave=np.array([1e-10] * len(data))

        new_data_ave = data_ave + alpha * (data - data_ave)

        return new_data_ave

    def draw_curve(self, count, data, index, draw_trig_mark=False):
        """
        Draw a waveform curve

        :param index:  count of curve for plotting
        :param data:   curve data for plotting
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

        xf = yf = None
        if self.fft or self.psd:
            if data_len == 0:
                return
            mode = "fft" if self.fft else "psd"
            xf, yf = self.calculate_ftt(data, sample_period, mode, self.fft_filter)

        if self.histogram and not self.psd and not self.fft:
            self.curves[count].opts['stepMode'] = True
        else:
            self.curves[count].opts['stepMode'] = False

        # Exponential moving average
        if self.average > 1:
            if yf is not None:
                yf = self.exponential_moving_average(yf, self.curves[count].plotdata_ave)
                self.curves[count].plotdata_ave = yf
            else:
                data = self.exponential_moving_average(data, self.curves[count].plotdata_ave)
                self.curves[count].plotdata_ave = data

        # Exponential moving average
        if self.average > 1:
            if yf is not None:
                yf = self.exponential_moving_average(yf, self.curves[count].plotdata_ave)
                self.curves[count].plotdata_ave = yf
            else:
                data = self.exponential_moving_average(data, self.curves[count].plotdata_ave)
                self.curves[count].plotdata_ave = data

        # Draw curve for the fft or psd mode
        if self.fft or self.psd:
            self.curves[count].setData(xf, yf)

        # Calculate histogram bins and draw the curve
        elif self.histogram and not self.psd and not self.fft:
            d = self.filter(data)
            y, x = np.histogram(d, bins=self.bins)
            self.curves[count].setData(x, y)

        # Draw waveform where X axis are indexes of data array which is drawn on Y axis
        elif time_array is None:
            data_to_plot = self.filter(data) + self.dc_offsets[index]
            self.curves[count].setData(data_to_plot)
            self.__handle_trigger_marker__(draw_trig_mark, self.max_length - self.samples_after_trig, [data_to_plot.min(), data_to_plot.max()])

        # Draw time_array on the X axis and data on Y
        else:
            d, t = self.filter(data, time_array)
            data_to_plot = d + self.dc_offsets[index]
            self.curves[count].setData(t - t[0], data_to_plot)
            self.__handle_trigger_marker__(draw_trig_mark, self.trigger_timestamp - time_array[0], [data_to_plot.min(), data_to_plot.max()])


    def __handle_trigger_marker__(self, draw_trig_mark, marktime, mark_size=None):
        """
        Draw vertical line trigger mark at the specified marktime.

        :param draw_trig_mark: (bool) Flag if trigger line should be drawn.
        :param marktime: (int) Sample number at which the trigger mark happened.
        :param mark_size: (Array [int, int]) Y range for the trigger mark.
        :return:
        """
        if self.trigger_mode and self.is_triggered:
            if draw_trig_mark:
                # Add trigger marker on plotting
                vr = self.plot.viewRange()[1]
                if vr[0] == 0 and vr[1] == 1:
                    min_value = max_value = None
                    if self.single_axis:
                        for field, value in self.trig_data.items():
                            if field in self.names:
                                a_min = np.amin(value).item()
                                a_max = np.amax(value).item()
                                min_value = a_min if min_value is None else min(min_value, a_min)
                                max_value = a_max if max_value is None else max(max_value, a_max)
                        mark_size = [min_value, max_value]
                    else:
                        mark_size = mark_size
                else:
                     mark_size = vr
                self.trigMarker.setData(np.array([marktime, marktime]),
                                        np.array(mark_size))
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

        # Do not update the drawing if image is frozen
        if self.is_freeze:
            return

        # Take ownership the self.data variable which holds all the waveforms
        self.wait()

        # Iterate over the names (channels) selected on the GUI and draw a line for each
        count = 0
        draw_trig_mark = True
        for idx, name in enumerate(self.names):
            if name != "None":
                try:
                    if self.trigger_mode:
                        data = self.trig_data[name]
                    else:
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

        # Trigger curves were drawn - Freeze the scope
        if self.trigger_mode and self.is_triggered:
            self.is_triggered = False
            self.trigger_data_done = True

        # Axis scaling
        if self.first_run or self.new_buffer or self.new_plot:
            # Perform auto range for the first time
            self.do_autoscale(auto_scale=True)
            self.first_run = False
            self.new_buffer = False
            self.new_plot = False
        # Then set it to the correct setting
        self.do_autoscale()

        self.update_fps()

        # Release the ownership on the self.data
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
