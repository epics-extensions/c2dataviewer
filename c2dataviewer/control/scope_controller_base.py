import numpy as np
import pyqtgraph
import pvaccess as pva
from ..model import ConnectionState
import math

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
        self.trigger_is_monitor = False
        self.trigger_auto_scale = False
        
        self._win.graphicsWidget.setup_plot(channels=channels, single_axis=True)
        
        # timer to update status with statistics data
        self.status_timer = pyqtgraph.QtCore.QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

    def set_trigger_pv(self, pvname):
        if self._win.graphicsWidget.plotting_started:
            self.notify_warning("Stop plotting first before changing trigger PV")
            return
                
        pvname = pvname.strip()
        if pvname == '':
            return
        
        proto = 'ca'
        name = pvname
        
        if "://" in name:
            proto, name = pvname.split("://")

        try:
            pvfields = self.model.update_trigger(name, proto=proto.lower())
            child = self.parameters.child("Trigger").child("Time Field")
            if proto == 'ca':
                child.hide()
                self._win.graphicsWidget.trigger.trigger_time_field = 'timeStamp'
            else:
                self._win.graphicsWidget.trigger.trigger_time_field = None
                pvfields.insert(0, 'None')
                child.show()
                child.setLimits(pvfields)
                child.setValue('None')                                
                                
        except Exception as e:
            self.notify_warning("Channel {}://{} timed out. \n{}".format(proto, name, repr(e)))
            

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
            self.set_trigger_pv(self.default_trigger)

        try:
            self.trigger_auto_scale = self.parameters.child("Trigger").child("Autoscale Buffer").value()
        except:
            pass
        
    def update_buffer(self, size):
        self._win.graphicsWidget.update_buffer(size)
        self.parameters.child("Acquisition").child("Buffer (Samples)").setValue(self._win.graphicsWidget.max_length)

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

                if childName == "Trigger.PV":
                    if data is None:
                        return
                    self.set_trigger_pv(data)
                elif childName == "Trigger.Mode":
                    self.set_trigger_mode(data)
                elif childName == "Trigger.Threshold":
                    self._win.graphicsWidget.trigger.trigger_level = data
                elif childName == "Trigger.Data Time Field":
                    self._win.graphicsWidget.trigger.data_time_field = data
                elif childName == "Trigger.Time Field":
                    self._win.graphicsWidget.trigger.trigger_time_field = data
                elif childName == "Trigger.Autoscale Buffer":
                    self.trigger_auto_scale = data
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

        self.stop_trigger()
        
        # Setup free run plotting
        if not self._win.graphicsWidget.trigger_mode():
            self.timer.timeout.connect(self._win.graphicsWidget.update_drawing)
            self.timer.start(self.refresh)
        else:
            self.start_trigger()

        self._win.graphicsWidget.notify_plotting_started(True)
        
    def stop_plotting(self):
        """

        :return:
        """
        self._win.graphicsWidget.notify_plotting_started(False)

        self.timer.stop()
        self.stop_trigger()
        
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
            self.new_buffer = True
            
    def set_trigger_mode(self, value):
        """
        Set trigger mode.
    
        :param value:
        :return:
        """
        trigger_mode = value != 'none'
        if trigger_mode != self._win.graphicsWidget.trigger_mode():
            if self._win.graphicsWidget.plotting_started:
                action = 'on' if trigger_mode else 'off'
                self.notify_warning('Stop plotting first before turning trigger %s' % (action))
                return
            
        self._win.graphicsWidget.set_trigger_mode(trigger_mode)
            
        trigger_type = None
        if trigger_mode:
            self._win.graphicsWidget.trigger.set_trigger_type(value)
            
    def start_trigger(self):
        """
        Process to start DAQ in trigger mode
            
        :return:
        """
        if not self.trigger_is_monitor:
            if self.model.trigger is None:
                raise Exception('Trigger PV is not set')
            
            if self._win.graphicsWidget.trigger.data_time_field is None:
                raise Exception('Data time field is not set')
            
            if self._win.graphicsWidget.trigger.trigger_time_field is None:
                raise Exception('Trigger time field is not set')
            
            self.model.start_trigger(self._win.graphicsWidget.trigger.data_callback)
            self.trigger_is_monitor = True

    def stop_trigger(self):
        """
        Stop trigger mode
        :return:
        """
        self.trigger_is_monitor = False
        self.model.stop_trigger()
        
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

        try:
            for q in self.parameters.child("Trigger").children():
                if q.name() == "Trig Status":
                    stat_str = 'Disconnected'
                    if self.trigger_is_monitor:
                        stat_str = self._win.graphicsWidget.trigger.status()
                    q.setValue(stat_str)
                elif q.name() == "Trig Value":
                    q.setValue(str(self._win.graphicsWidget.trigger.trigger_value))
        except:
            pass

        #handle any auto-adjustments
        if self.trigger_auto_scale and self._win.graphicsWidget.trigger_mode():
            if self._win.graphicsWidget.trigger.missed_triggers > 0:
                newsize = self._win.graphicsWidget.trigger.missed_adjust_buffer_size

                # Round up to 3 10's places
                # ex. 12345 would be rounded to 12400
                precision = 3
                exp = math.ceil(math.log10(newsize))
                roundunit = 10**max(exp - precision, 0)
                newsize = math.ceil(newsize / roundunit) * roundunit

                self.update_buffer(newsize)
            
        
