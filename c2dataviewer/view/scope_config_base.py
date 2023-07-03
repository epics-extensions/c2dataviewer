"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

class ScopeConfigureBase:
    def __init__(self, params, **kwargs):
        self.params = params
        self.default_trigger = kwargs.get("trigger", None)

    def add_source_aquisition_props(self, children, section):
        """
        Add acquisition information specific to the application data source.  This
        should be implemented by the child class
        """
        return children

    def assemble_acquisition(self, section=None, buffer_unit='Samples'):
        """
        Assemble acquisition information

        :param section:
        :return:
        """

        children = []

        buffer_size = None
        try:
            buffer_size = section["BUFFER"]
        except:
            pass
        
        children += [
            {"name": "Freeze", "type": "bool", "value": False},
            {"name": "Buffer (%s)" % buffer_unit, "type": "int", "value": buffer_size, "siPrefix": False, 'decimals': 20}
        ]

        acquisition = {"name": "Acquisition", "type":"group", "children": children}
        
        return acquisition

    
    def assemble_display(self, section=None, autoscale=None):
        """
        Assemble display information

        :param section:
        :return:
        """
        if section is None:
            display = {"name": "Display", "type": "group", "children": [
                {"name": "Mode", "type": "list", "values": {
                    "Normal": "normal",
                    "FFT": "fft",
                    "PSD": "psd",
                    "Diff": "diff",
                    "X vs Y": "xy",
                }, "value": "Normal"},
                {"name": "FFT filter", "type": "list", "values": {
                    "None" : "none",
                    "Hamming" : "hamming"
                }, "value": "None"},
                {"name": "Exp moving avg", "type": "int", "value": 1, "limits" : (1, 1e+10)},
                {"name": "Autoscale", "type": "bool", "value": autoscale},
                {"name": "Single axis", "type": "bool", "value": True},
                {"name": "Histogram", "type": "bool", "value": False},
                {"name": "Num Bins", "type": "int", "value": 100},
                {"name": "Refresh", "type": "float", "value": 0.1, "siPrefix": True, "suffix": "s"},
            ]}
        else:
            display_mode = section.get("MODE", "normal").lower().strip()
            if display_mode not in ["normal", "fft", "psd", "diff", "xy"]:
                display_mode = "normal"

            fft_filter = section.get("FFT_FILTER", None)
            if fft_filter is not None:
                if fft_filter.lower().strip() in ["none", "hamming"]:
                    fft_filter = fft_filter.lower().strip().capitalize()
                else:
                    # Disable filter if config not valid
                    fft_filter = "none"

            try:
                n_average = section.getint("AVERAGE", 1)
                n_average = n_average if n_average > 0 else 1
            except ValueError:
                n_average = 1

            if autoscale is not None:
                if str(autoscale).upper().strip() in ["TRUE"]:
                    autoscale = True
                else:
                    autoscale = False
            else:
                #unreacheable code
                pass

            single_axis = section.get("SINGLE_AXIS", None)
            if single_axis is not None:
                if single_axis.upper().strip() in ["FALSE"]:
                    single_axis = False
                else:
                    single_axis = True
            else:
                single_axis = True

            histogram = section.get("HISTOGRAM", None)
            if histogram is not None:
                if histogram.upper().strip() in ["TRUE"]:
                    histogram = True
                else:
                    # set auto scale value to None if a "None" string comes from configuration
                    histogram = False
            else:
                histogram = False

            try:
                n_binning = section.getint("N_BIN", 100)
            except ValueError:
                n_binning = 1

            try:
                refresh = section.getfloat("REFRESH", 100)
            except ValueError:
                refresh = 1

            display = {"name": "Display", "type": "group", "children": [
                {"name": "Mode", "type": "list", "values": {
                    "Normal": "normal",
                    "FFT": "fft",
                    "PSD": "psd",
                    "Diff": "diff",
                    "X vs Y": "xy",
                }, "value": display_mode},
                {"name": "FFT filter", "type": "list", "values": {
                    "None" : "none",
                    "Hamming" : "hamming"
                }, "value": fft_filter},
                {"name": "Exp moving avg", "type": "int", "value": n_average, "limits" : (1, 1e+10)},
                {"name": "Autoscale", "type": "bool", "value": autoscale},
                {"name": "Single axis", "type": "bool", "value": single_axis},
                {"name": "Histogram", "type": "bool", "value": histogram},
                {"name": "Num Bins", "type": "int", "value": n_binning},
                {"name": "Refresh", "type": "float", "value": refresh / 1000., "siPrefix": True, "suffix": "s"},
            ]}

        return display


    def assemble_trigger(self, section=None):
        trigger_pv = self.default_trigger
        trigger_mode = 'none'

        if section:
            # Trigger PV name and protocol, which comes with format of proto://pv_name
            # the protocol is either ca:// for channel access or pva:// for pvAccess
            trigger_pv = section.get("TRIGGER", None)
            if self.default_trigger is not None:
                trigger_pv = self.default_trigger

            if trigger_pv is not None and trigger_pv.upper().strip() == "NONE":
                # set trigger PV value to None if a "None" string comes from configuration
                trigger_pv = None
            if trigger_pv is None:
                trigger_mode = None
            else:
                trigger_mode = section.get("TRIGGER_MODE", None)
            if trigger_mode is not None:
                trigger_mode = trigger_mode.lower().strip()
                if trigger_mode == 'off':
                    trigger_mode = 'none'
            else:
                trigger_mode = 'none'
        
        cfg ={"name": "Trigger",
              "type": "group",
              "children" : [
                  { "name" :  "Mode", "type": "list", "values": {
                    "Off" : "none",
                    "On change" : "onchange",
                    "Greater than threshold" : "gtthreshold",
                    "Lesser than threshold" : "ltthreshold"
                    },
                  "value" : trigger_mode
                 },
                  {"name": "PV", "type": "str", "value": trigger_pv},
                  {"name": "Trig Status", "type": "str", "value": "", "readonly": True},
                  {"name": "Trig Value", "type": "str", "value": "", "readonly": True},
                  {"name": "Time Field", "type": "list", "values" :
                   [ "None" ], "default" : "None", "visible" : False},
                  {"name": "Data Time Field", "type": "list", "values" :["None"], "default" : "None" },
                  {"name": "Autoscale Buffer", "type": "bool", "value" : True},
                  {"name": "Threshold", "type": "float", "value": 0.0},
              ]}
        return cfg
        
    def assemble_statistics(self):
        statistics = {"name": "Statistics", "type": "group", "children": [
            {"name": "CPU", "type": "float", "value": 0, "readonly": True, "suffix": "%"},
            {"name": "Lost Arrays", "type": "int", "value": 0, "readonly": True},
            {"name": "Tot. Arrays", "type": "int", "value": 0, "readonly": True, "siPrefix": True},
            {"name": "Arrays/Sec", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
             "suffix": "/sec"},
            {"name": "Bytes/Sec", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
             "suffix": "/sec"},
            {"name": "Rate", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
             "suffix": "Frames/sec"},
        ]}
        return statistics
