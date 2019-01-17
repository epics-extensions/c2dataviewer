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
    def __init__(self, params, pvs=None):
        """

        :param params: parameters parsed from command line and configuration file
        :param pvs: pv name dictionary, format: {"alias": "PV:Name"}
        """
        self.params = params
        self.pvs = pvs
        self.counts = 4

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
        self.default_color = ['#FFFF00', '#FF00FF', '#55FF55', '#00FFFF', '#5555FF',
                         '#5500FF', '#FF5555', '#0000FF', '#FFAA00', '#000000']
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
                {"name": "TrigPV", "type": "str", "value": None},
                {"name": "TriggerMode", "type": "bool", "value": False},
                {"name": "PostTrigger", "type": "float", "value": 0.0, "siPrefix": True, "suffix": "Second"},
                {"name": "HoldTrigger", "type": "float", "value": 0.0, "siPrefix": True, "suffix": "Second"},
                # {"name": "Freeze", "type": "bool", "value": False},
                {"name": "Buffer", "type": "int", "value": 256, "siPrefix": True, "suffix": "Samples"},
                {"name": "Start", "type": "bool", "value": False}
            ]}
        else:
            # Trigger PV name and protocol, which comes with format of proto://pv_name
            # the protocol is either ca:// for channel access or pva:// for pvAccess
            trigger_pv = section.get("TRIGGER", None)

            if trigger_pv is not None and trigger_pv.upper().strip() == "NONE":
                # set trigger PV value to None if a "None" string comes from configuration
                trigger_pv = None
            trigger_mode = section.get("WAIT_TRIGGER", None)
            if trigger_mode is not None:
                if trigger_mode.upper().strip() in ["TRUE"]:
                    trigger_mode = True
                else:
                    # set trigger PV value to None if a "None" string comes from configuration
                    trigger_mode = False
            else:
                trigger_mode = False

            post_trigger_pause = 0.0
            try:
                post_trigger_pause = section.getfloat("POST_TRIGGER_PAUSE", 0.0)
            except ValueError:
                pass
            trigger_holdoff = 0.0
            try:
                trigger_holdoff = section.getfloat("TRIGGER_HOLDOFF", 0.0)
            except ValueError:
                pass

            # freeze = section.get("FREEZE", None)
            # if freeze is not None:
            #     if freeze.upper().strip() in ["TRUE"]:
            #         freeze = True
            #     else:
            #         # set trigger PV value to None if a "None" string comes from configuration
            #         freeze = False
            # else:
            #     freeze = False

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
            acquisition = {"name": "Acquisition", "type": "group", "children": [
                # EPICS7 PV name, which assumes pvAccess protocol
                # Alias name to be supported later
                {"name": "PV", "type": "str", "value": pv},

                {"name": "TrigPV", "type": "str", "value": trigger_pv},
                {"name": "TriggerMode", "type": "bool", "value": trigger_mode},
                {"name": "PostTrigger", "type": "float", "value": post_trigger_pause, "siPrefix": True,
                 "suffix": "Second"},
                {"name": "HoldTrigger", "type": "float", "value": trigger_holdoff, "siPrefix": True,
                 "suffix": "Second"},
                # {"name": "Freeze", "type": "bool", "value": freeze},
                {"name": "Buffer (Samples)", "type": "int", "value": buffer, "siPrefix": False, 'decimals': 20} ,# "suffix": "Samples"},
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
                    "X vs Y": "x_vs_y",
                }, "value": "Normal"},
                {"name": "N Ave", "type": "int", "value": 1},
                {"name": "Autoscale", "type": "bool", "value": False},
                {"name": "Histogram", "type": "bool", "value": False},
                {"name": "Num Bins", "type": "int", "value": 100},
                {"name": "Refresh", "type": "float", "value": 0.1, "siPrefix": True, "suffix": "s"},
            ]}
        else:
            try:
                n_average = section.getint("AVERAGE", 1)
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
                    "X vs Y": "x_vs_y",
                }, "value": "Normal"},
                {"name": "N Ave", "type": "int", "value": n_average},
                {"name": "Autoscale", "type": "bool", "value": autoscale},
                {"name": "Histogram", "type": "bool", "value": histogram},
                {"name": "Num Bins", "type": "int", "value": n_binning},
                {"name": "Refresh", "type": "float", "value": refresh / 1000., "siPrefix": True, "suffix": "s"},
            ]}

        return display

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

        # line up in order
        paramcfg = [acquisition, display]
        for ch in channel:
            paramcfg.append(ch)
        statistics = {"name": "Statistics", "type": "group", "children": [
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
