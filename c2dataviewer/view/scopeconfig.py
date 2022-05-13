# -*- coding: utf-8 -*-

from .scope_config_base import ScopeConfigureBase
import logging
"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""


class Configure(ScopeConfigureBase):
    """
    Scope application configuration panel settings
    """
    def __init__(self, params, **kwargs):
        """

        :param params: parameters parsed from command line and configuration file
        :param pvs: pv name dictionary, format: {"alias": "PV:Name"}
        """
        super().__init__(params, show_start=True, **kwargs)
        self.pvs = kwargs.get("pv", None)

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

    def add_source_acquisition_props(self, children, section):
        pv = None
        if self.pvs is not None:
            pv = list(self.pvs.values())[0]

        if section:
            if pv is None:
                # it means PV map is not specified from command line
                # get one from configuration
                pv = pv if pv is not None else section.get("PV", None)
                if pv is not None:
                    # if PV is available by default
                    self.pvs = {pv: pv}

        newchildren = [
            # EPICS7 PV name, which assumes pvAccess protocol
            # Alias name to be supported later
            {"name": "PV", "type": "str", "value": pv},
            {"name": "PV status", "type": "str", "value": "Disconnected", "readonly": True}
        ]

        newchildren += children
        return newchildren

    def assemble_config(self):
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
        return cfg

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
            if "TRIGGER" in sections:
                trigger = self.assemble_trigger(self.params["TRIGGER"])
            else:
                trigger = self.assemble_trigger()
        except KeyError as e:
            if str(e) not in ["'SCOPE'"]:
                logging.getLogger().warning('Key %s not found in config' %  (str(e)))
            acquisition = self.assemble_acquisition()
            display = self.assemble_display()
            channel = self.assemble_channel()
            trigger = self.assemble_trigger()
            
        if acquisition is None or display is None or channel is None:
            raise RuntimeError("No enough information for scope")

        
        cfg = self.assemble_config()

        
        # line up in order
        paramcfg = [acquisition, trigger, display, cfg]
        for ch in channel:
            paramcfg.append(ch)
        statistics = self.assemble_statistics()
        
        paramcfg.append(statistics)

        return paramcfg
