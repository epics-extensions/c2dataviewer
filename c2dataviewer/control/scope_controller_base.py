import numpy as np
import pyqtgraph
import pvaccess as pva
from ..model import ConnectionState

class ScopeControllerBase:
    def __init__(self, widget, model, parameters, warning, channels=[], **kwargs):
        self._win = widget
        self.model = model
        self.parameters = parameters
        self.data = None
        # refresh frequency: every 100 ms by default
        self.refresh = 100

        self.plotting_started = False

        self.timer = pyqtgraph.QtCore.QTimer()
        self.timer.timeout.connect(self._win.graphicsWidget.update_drawing)
        self._win.graphicsWidget.set_model(self.model)

        self._warning = warning
        self._warning.warningConfirmButton.clicked.connect(lambda: self.accept_warning())

        self.arrays = np.array([])
        self.lastArrays = 0

        self.default_arrayid = "None"
        self.default_xaxes = "None"
        self.current_arrayid = "None"
        self.current_xaxes = "None"
        self.default_trigger = None

        self._win.graphicsWidget.setup_plot(channels=channels, single_axis=True)
        
        # timer to update status with statistics data
        self.status_timer = pyqtgraph.QtCore.QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

    def default_config(self, **kwargs):
        """
        Default configuration for array ID and x axes field names

        :param kwargs:
        :return:
        """
        self.default_arrayid = kwargs.get("arrayid", None)
        if self.default_arrayid is None:
            self.default_arrayid = "None"
        else:
            self._win.graphicsWidget.set_arrayid(self.default_arrayid)
        self.default_xaxes = kwargs.get("xaxes", None)
        if self.default_xaxes is None:
            self.default_xaxes = "None"
        else:
            self._win.graphicsWidget.set_xaxes(self.default_xaxes)
        self._win.graphicsWidget.set_range(**kwargs)

        max_length = self.parameters.child("Acquisition").child("Buffer (Samples)").value()
        if max_length:
            self._win.graphicsWidget.update_buffer(int(max_length))
            
        self._win.graphicsWidget.set_binning(self.parameters.child("Display").child("Num Bins").value())

        refresh = self.parameters.child("Display").child("Refresh").value()
        if refresh:
            self.set_freshrate(refresh)
            
        self.default_trigger = kwargs.get("trigger", None)
        if self.default_trigger is not None:
            try:
                if "://" in self.default_trigger:
                    # pv comes with format of proto://pvname
                    p, name = self.default_trigger.split("://")
                    trt = self.model.update_trigger(name, proto=p.lower())
                else:
                    # PV name only, use default Channel Access protocol
                    trt = self.model.update_trigger(self.default_trigger)
                self.parameters.child("Acquisition").child('Trigger Mode').setWritable()
                self._win.graphicsWidget.trigger_rec_type = trt
                self.__trigger_level_rw__(trt)
            except Exception as e:
                self._win.graphicsWidget.trigger_rec_type = None
                self.parameters.child("Acquisition").child('Trigger PV').setValue("")
                self.parameters.child("Acquisition").child('Trigger Mode').setReadonly()
                self.default_trigger = None
                raise e

            
    def update_buffer(self, size):
        self._win.graphicsWidget.update_buffer(size)
        self.parameters.child("Acquisition").child("Buffer (Samples)").setValue(self._win.graphicsWidget.max_length)


    def __trigger_level_rw__(self, trt):
        """
        Set trigger level parameter readable/writable according trigger record type.
            
        Making trigger level writable is not supported in pyqtgraph 0.10. See
        https://github.com/pyqtgraph/pyqtgraph/issues/263
        This was fixed with 0.11, but we had other issues with the new version. See
        https://git.aps.anl.gov/C2/conda/data-viewer/-/merge_requests/30#note_4799
            
        :param trt: (string) Record type as string (e.g. ai, bi, calc, ...).
        :return:
        """
        pass
    # if trt in ["ai", "ao"]:
    #     self.parameters.child("Acquisition").child('Trigger Threshold').setWritable()
    # else:
    #     self.parameters.child("Acquisition").child('Trigger Threshold').setReadonly()

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

                if childName == "Acquisition.Trigger PV":
                    if data is None:
                        return
                    if self._win.graphicsWidget.plotting_started:
                        self.notify_warning("Please stop plotting first before changing trigger PV")
                        return
                    data = data.strip()
                    if data != "":
                        try:
                            if "://" in data:
                                # pv comes with format of proto://pvname
                                p, name = data.split("://")
                                trt = self.model.update_trigger(name, proto=p.lower())
                            else:
                                # PV name only, use default Channel Access protocol
                                trt = self.model.update_trigger(data)
                                self.parameters.child("Acquisition").child('Trigger Mode').setWritable()
                                self._win.graphicsWidget.trigger_rec_type = trt
                                self.__trigger_level_rw__(trt)

                            # restart trigger if trigger is enabled
                            if self._win.graphicsWidget.trigger_mode:
                                self.stop_trigger_mode()
                                self.start_trigger_mode()
                        except RuntimeError as e:
                            self._win.graphicsWidget.trigger_rec_type = None
                            self.notify_warning(repr(e))
                            self.parameters.child("Acquisition").child('Trigger Mode').setReadonly()
                            self.stop_trigger_mode()
                            # TODO clear trigger PV text field
                        except Exception as e:
                            self._win.graphicsWidget.trigger_rec_type = None
                            self.notify_warning("Channel {} timed out. \n{}".format(data, repr(e)))
                            self.stop_trigger_mode()
                            # TODO clear trigger PV text field
                elif childName == "Acquisition.Trigger Mode":
                    self.set_trigger_mode(data)
                elif childName == "Acquisition.Trigger Threshold":
                    self._win.graphicsWidget.trigger_level = data
                elif childName == "Acquisition.PostTrigger":
                    self.set_post_tigger(data)
                elif childName == "Acquisition.HoldTrigger":
                    self.set_hold_trigger(data)
                elif childName == "Acquisition.Buffer (Samples)":
                    self._win.graphicsWidget.update_buffer(data)
                elif childName == "Acquisition.Freeze":
                    self._win.graphicsWidget.is_freeze = data
                elif childName == "Display.Mode":
                    self._win.graphicsWidget.set_display_mode(data)
                    self._win.graphicsWidget.setup_plot()
                    # Disable multiaxis for the FFT and PSD modes. As at the time of the
                    # writing this code pyqtgraph does not support logarithmic scale in multiaxis configuration.
                    if self._win.graphicsWidget.fft or self._win.graphicsWidget.psd:
                        self.parameters.child("Display").child("Single axis").setReadonly()
                    else:
                        self.parameters.child("Display").child("Single axis").setWritable()
                elif childName == "Display.FFT filter":
                    self._win.graphicsWidget.set_fft_filter(data)
                elif childName == "Display.Exp moving avg":
                    self._win.graphicsWidget.set_average(data)
                elif childName == "Display.Autoscale":
                    self._win.graphicsWidget.set_autoscale(data)
                elif childName == "Display.Single axis":
                    self._win.graphicsWidget.setup_plot(single_axis=data)
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

    def set_freshrate(self, value):
        """
        Set time to refresh
            
        :param value: time interval to plot, in second
        :return:
        """
        plotting_started = self._win.graphicsWidget.plotting_started
        self.stop_plotting()
        self.refresh = value*1000.0
        if plotting_started:
            self.start_plotting()


    def start_plotting(self):
        """
            
        :return:
        """
        try:
            self.timer.timeout.disconnect()
            self.timer.stop()
        except Exception:
            pass

        # Disable trigger signal
        if self._win.graphicsWidget.plot_trigger_signal_emitter is not None:
            try:
                self._win.graphicsWidget.plot_trigger_signal_emitter.my_signal.disconnect()
            except Exception:
                pass

        # Setup free run plotting
        if not self._win.graphicsWidget.trigger_mode:
            self.timer.timeout.connect(self._win.graphicsWidget.update_drawing)
            self.timer.start(self.refresh)

        # Setup trigger plotting
        if self._win.graphicsWidget.trigger_mode and self._win.graphicsWidget.plot_trigger_signal_emitter is not None:
            self._win.graphicsWidget.plot_trigger_signal_emitter.my_signal.connect(self._win.graphicsWidget.update_drawing)

        self._win.graphicsWidget.plotting_started = True
                
    def stop_plotting(self):
        """

        :return:
        """
        self._win.graphicsWidget.plotting_started = False

        # Stop timer
        self.timer.stop()

        # Stop signal emitter for trigger mode
        if self._win.graphicsWidget.plot_trigger_signal_emitter is not None:
            try:
                self._win.graphicsWidget.plot_trigger_signal_emitter.my_signal.disconnect()
            except Exception:
                pass

            
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
            self._win.graphicsWidget.current_xaxes = value

    def set_trigger_mode(self, value):
        """
        Set trigger mode.
    
        :param value:
        :return:
        """
        self.stop_plotting()
        self._win.graphicsWidget.trigger_mode = value
        if not self._win.graphicsWidget.trigger_mode:
            self._win.graphicsWidget.trigger_data_done = True

        if self.model.trigger_chan is not None:
            if self._win.graphicsWidget.trigger_mode:
                self.start_trigger_mode()
            else:
                self.stop_trigger_mode()
        else:
            self.parameters.child("Acquisition").child('Trigger Mode').setReadonly()

        if self._win.graphicsWidget.plotting_started:
            self.start_plotting()

    def start_trigger_mode(self):
        """
        Process to start DAQ in trigger mode
            
        :return:
        """
        self._win.graphicsWidget.samples_after_trig_cnt = 0

        if not self._win.graphicsWidget.trigger_is_monitor:
            try:
                self.model.start_trigger(self._win.graphicsWidget.trigger_process)
                self._win.graphicsWidget.trigger_count = 0
                self._win.graphicsWidget.trigger_is_monitor = True
            except Exception as e:
                self._win.graphicsWidget.trigger_is_monitor = False
                raise e

        self._win.graphicsWidget.is_triggered = False

    def stop_trigger_mode(self):
        """
        Stop trigger mode
        :return:
        """
        self._win.graphicsWidget.trigger_is_monitor = False
        self._win.graphicsWidget.trigger_count = 0
        if self.model.trigger_chan is not None:
            self.model.stop_trigger()

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

    def accept_warning(self):
        """
            
        :return:
        """
        self._warning.close()

    def notify_warning(self, msg):
        #close previous warning
        self.accept_warning()
            
        self._warning.warningTextBrowse.setText(msg)
        self._warning.show()

        
    def update_status(self):
        """
        Update statistics status.
            
        :return:
        """
        # Update display
        single_axis_child = self.parameters.child("Display", "Single axis")
        if single_axis_child.value() != self._win.graphicsWidget.single_axis:
            single_axis_child.setValue(self._win.graphicsWidget.single_axis)

        # Update statistics
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
                self._win.graphicsWidget.monitoring_trigger = False
                if self._win.graphicsWidget.monitoring_trigger:
                    stat_str = "Not Trig Mode, Monitoring Trigger PV"
                    if self._win.graphicsWidget.trigger_mode:
                        stat_str = "Waiting for Trigger, Collecting"
                        if self._win.graphicsWidget.is_triggered:
                            stat_str = "Got Trigger, Collecting"
                            if self._win.graphicsWidget.trigger_data_done:
                                stat_str = "Got Trigger, Done Collecting"
                q.setValue(stat_str)
