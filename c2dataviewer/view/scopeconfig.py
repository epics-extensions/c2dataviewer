# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""


class Configure:
    """
    Scope application configuration panel settings
    """
    def __init__(self, params, **kwargs):
        """

        :param params: parameters parsed from command line and configuration file
        :param pvs: pv name dictionary, format: {"alias": "PV:Name"}
        """
        self.params = params
        self.pvs = kwargs.get("pv", None)
        self.default_arrayid = kwargs.get("arrayid", "None")
        self.default_xaxes = kwargs.get("xaxes", "None")
        self.default_trigger = kwargs.get("trigger", None)

        self.counts = 4
        self.default_color = ['#FFFF00', '#FF00FF', '#55FF55', '#00FFFF', '#5555FF',
                              '#5500FF', '#FF5555', '#0000FF', '#FFAA00', '#000000']

    def assemble_channel(self, section=None):
        """
        Assemble channel information for plotting

        :param section:
        :return:
        """
        if section is None:
            self.counts = 4
        else:
            # get channel counts to display, 4 by default
            try:
                self.counts = section.getint('COUNT', 4)
                if self.counts > 10:
                    # limit max channel to display
                    self.counts = 10
            except ValueError:
                # TODO: add logging information
                self.counts = 4

        channel = []
        for i in range(self.counts):
            channel.append(
                {"name": "Channel %s" % (i + 1),
                 "type": "group",
                 "children": [
                     {
                         "name": "Color",
                         "type": "color",
                         "value": self.default_color[i],
                         "readonly": True
                     },
                     {"name": "Field", "type": "list", "values": [], "value": "None"},
                     {"name": "DC offset", "type": "float", "value": 0.0},
                     {"name": "Axis location", "type": "list", "values": {
                         "Left" : "left",
                         "Right" : "right",
                     }, "value" : "Left"},
                 ]
                 }
            )

        return channel

    def assemble_acquisition(self, section=None):
        """
        Assemble acquisition information

        :param section:
        :return:
        """
        pv = None
        if self.pvs is not None:
            pv = list(self.pvs.values())[0]
        if section is None:
            acquisition = {"name": "Acquisition", "type": "group", "children": [
                # EPICS7 PV name, which assumes pvAccess protocol
                # Alias name to be supported later
                {"name": "PV", "type": "str", "value": pv},
                {"name": "Trigger PV", "type": "str", "value": self.default_trigger},
                {"name": "Trigger Mode", "type": "bool", "value": False, "readonly": True},
                {"name": "Trigger Threshold", "type": "float", "value": 0.0},
                # {"name": "PostTrigger", "type": "float", "value": 0.0, "siPrefix": True, "suffix": "Second"},
                # {"name": "HoldTrigger", "type": "float", "value": 0.0, "siPrefix": True, "suffix": "Second"},
                {"name": "Freeze", "type": "bool", "value": False},
                {"name": "Buffer (Samples)", "type": "int", "value": 256, "siPrefix": True, "suffix": "Samples"},
                {"name": "Start", "type": "bool", "value": False}
            ]}
        else:
            buffer = 256
            try:
                buffer = section.getint("BUFFER", 256)
            except ValueError:
                pass

            if pv is None:
                # it means PV map is not specified from command line
                # get one from configuration
                pv = pv if pv is not None else section.get("PV", None)
                if pv is not None:
                    # if PV is available by default
                    self.pvs = {pv: pv}

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
                trigger_mode = section.get("WAIT_TRIGGER", None)
            if trigger_mode is not None:
                if trigger_mode.upper().strip() in ["TRUE"]:
                    trigger_mode = True
                else:
                    # set trigger PV value to None if a "None" string comes from configuration
                    trigger_mode = False
            else:
                trigger_mode = False

            trigger_mode_disabled = True
            if trigger_mode:
                trigger_mode_disabled = False

            # post_trigger_pause = 0.0
            # try:
            #     post_trigger_pause = section.getfloat("POST_TRIGGER_PAUSE", 0.0)
            # except ValueError:
            #     pass
            # trigger_holdoff = 0.0
            # try:
            #     trigger_holdoff = section.getfloat("TRIGGER_HOLDOFF", 0.0)
            # except ValueError:
            #     pass

            acquisition = {"name": "Acquisition", "type": "group", "children": [
                # EPICS7 PV name, which assumes pvAccess protocol
                # Alias name to be supported later
                {"name": "PV", "type": "str", "value": pv},
                {"name": "Trigger PV", "type": "str", "value": trigger_pv},
                {"name": "Trigger Mode", "type": "bool", "value": trigger_mode, "readonly": trigger_mode_disabled},
                # Due to issue: https://github.com/pyqtgraph/pyqtgraph/issues/263
                # always make the trigger level writable instead of disabling writing
                {"name": "Trigger Threshold", "type": "float", "value": 0.0},
                # {"name": "PostTrigger", "type": "float", "value": post_trigger_pause, "siPrefix": True,
                #  "suffix": "Second"},
                # {"name": "HoldTrigger", "type": "float", "value": trigger_holdoff, "siPrefix": True,
                #  "suffix": "Second"},
                {"name": "Freeze", "type": "bool", "value": False},
                {"name": "Buffer (Samples)", "type": "int", "value": buffer, "siPrefix": False, 'decimals': 20},
                {"name": "Start", "type": "bool", "value": False}
            ]}

        return acquisition

    def assemble_display(self, section=None):
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
                {"name": "Autoscale", "type": "bool", "value": False},
                {"name": "Single axis", "type": "bool", "value": True},
                {"name": "Histogram", "type": "bool", "value": False},
                {"name": "Num Bins", "type": "int", "value": 100},
                {"name": "Refresh", "type": "float", "value": 0.1, "siPrefix": True, "suffix": "s"},
            ]}
        else:

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

            autoscale = section.get("AUTOSCALE", None)
            if autoscale is not None:
                if autoscale.upper().strip() in ["TRUE"]:
                    autoscale = True
                else:
                    # set auto scale value to None if a "None" string comes from configuration
                    autoscale = False
            else:
                autoscale = False

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
                }, "value": "Normal"},
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

    def assemble_config(self):
        """


        :return:
        """
        config = {}

        return config

    def parse(self):
        """

        :return:
        """
        try:
            sections = self.params["SCOPE"]["SECTION"].split(",")
            for idx, section in enumerate(sections):
                # remove unnecessary space
                sections[idx] = section.strip()
            if "ACQUISITION" in sections:
                acquisition = self.assemble_acquisition(self.params["ACQUISITION"])
            else:
                acquisition = self.assemble_acquisition()
            if "DISPLAY" in sections:
                display = self.assemble_display(self.params["DISPLAY"])
            else:
                display = self.assemble_display()
            if "CHANNELS" in sections:
                channel = self.assemble_channel(self.params["CHANNELS"])
            else:
                channel = self.assemble_channel()
        except KeyError:
            acquisition = self.assemble_acquisition()
            display = self.assemble_display()
            channel = self.assemble_channel()

        if acquisition is None or display is None or channel is None:
            raise RuntimeError("No enough information for scope")

        # Assemble extra configuration information for plotting
        # which is ArrayId selection, and x axes
        id_value = ["None"]
        if self.default_arrayid != "None":
            id_value.append(self.default_arrayid)
        axes = ["None"]
        if self.default_xaxes != "None":
            axes.append(self.default_xaxes)

        cfg = {"name": "Config",
               "type": "group",
               "children": [
                   {"name": "ArrayId", "type": "list", "values": id_value, "value": self.default_arrayid},
                   {"name": "X Axes", "type": "list", "values": axes, "value": self.default_xaxes},
               ]
               }

        # line up in order
        paramcfg = [acquisition, display, cfg]
        for ch in channel:
            paramcfg.append(ch)
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
            {"name": "TrigStatus", "type": "str", "value": "", "readonly": True},
        ]}

        paramcfg.append(statistics)

        return paramcfg
