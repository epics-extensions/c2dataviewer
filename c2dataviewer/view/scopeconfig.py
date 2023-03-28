# -*- coding: utf-8 -*-

from .scope_config_base import ScopeConfigureBase
import logging
import re

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

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
        super().__init__(params, **kwargs)
        self.pvs = kwargs.get("pv", None)

        self.counts = 4
        self.default_color = ['#FFFF00', '#FF00FF', '#55FF55', '#00FFFF', '#5555FF',
                              '#5500FF', '#FF5555', '#0000FF', '#FFAA00', '#000000']
        
        self.default_arrayid = kwargs.get("arrayid", "None")
        self.default_xaxes = kwargs.get("xaxes", "None")

        
    def assemble_channel(self, section=None):
        """
        Assemble channel information for plotting

        :param section:
        :return:
        """
        # get channel counts to display, 4 by default
        if section is None:
            self.counts = 4
        else:
            self.counts = section.getint('COUNT', 4)

        channel = []

        #Read channel information.  Channel order is
        #determined by order in config
        chan_cfg_lookup = {}
        
        if section:
            for k, v in section.items():
                if bool(re.match('chan', k, re.I)):
                    ch, param = k.lower().split('.')
                    chan_cfg_lookup[ch] = chan_cfg_lookup.get(ch, {})
                    chan_cfg_lookup[ch][param] = v

        chan_cfgs = list(chan_cfg_lookup.values())
        
        if len(chan_cfgs) > self.counts:
            self.counts = len(chan_cfgs)

        if self.counts > 10:
            # limit max channel to display
            self.counts = 10

        
        for i in range(self.counts):
            default_cfg = {
                'field' : 'None',
                'dcoffset': 0.0
            }
            
            chcfg = chan_cfgs[i] if len(chan_cfgs) > i else default_cfg

            field = chcfg.get('field', default_cfg['field'])
            dcoffset = float(chcfg.get('dcoffset', default_cfg['dcoffset']))
                                 
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
                     {"name": "Field", "type": "list", "values": [], "value": field},
                     {"name": "DC offset", "type": "float", "value": dcoffset},
                     {"name": "Axis location", "type": "list", "values": {
                         "Left" : "left",
                         "Right" : "right",
                     }, "value" : "Left"},
                 ]
                 }
            )

        return channel

    def assemble_acquisition(self, section=None):
        buffer_unit = 'samples'
        try:
            buffer_unit = section["BUFFERUNIT"]
        except:
            pass

        if buffer_unit.lower() not in ["samples", "objects"]:
            buffer_unit = 'samples'

        buffer_unit = buffer_unit.title()

        acquisition = super().assemble_acquisition(section, buffer_unit=buffer_unit)
        children = acquisition['children']

        start = False
        if section:
            start = section.getboolean('ConnectOnStart', False)

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
            {"name": "Buffer Unit", "type": "list", "values": ["Samples", "Objects"],
             "value": buffer_unit},
            {"name": "PV", "type": "str", "value": pv},
            {"name": "PV status", "type": "str", "value": "Disconnected", "readonly": True},
            {"name": "Start", "type": "bool", "value": start}
        ]

        children.extend(newchildren)
        
        return acquisition

    def assemble_statistics(self):
        stats = super().assemble_statistics()
        children = stats['children']
        children.append( {"name": "Avg Samples/Obj", "type": "float", "value": 0, "readonly":True, "decimals":20})
        return stats
    
    def assemble_config(self, section=None):
        # Assemble extra configuration information for plotting
        # which is ArrayId selection, and x axes
        id_value = ["None"]
        if self.default_arrayid != "None":
            id_value.append(self.default_arrayid)
        axes = ["None"]
        self.default_xaxes = section.get("XAXES", "None") if section else "None"
        if self.default_xaxes != "None":
            axes.append(self.default_xaxes)

        self.default_major_tick = section.getint('MAJORTICKS', 0) if section else 0
        self.default_minor_tick = section.getint('MINORTICKS', 0) if section else 0
        
        cfg = {"name": "Config",
               "type": "group",
               "children": [
                   {"name": "ArrayId", "type": "list", "values": id_value, "value": self.default_arrayid},
                   {"name": "X Axes", "type": "list", "values": axes, "value": self.default_xaxes},
                   {"name": "Major Ticks", "type": "int", "value": self.default_major_tick, 'decimals':20},
                   {"name": "Minor Ticks", "type": "int", "value": self.default_minor_tick, 'decimals':20},
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
            if "CONFIG" in sections:
                cfg = self.assemble_config(self.params["CONFIG"])
            else:
                cfg = self.assemble_config()
                                           
        except KeyError as e:
            if str(e) not in ["'SCOPE'"]:
                logging.getLogger().warning('Key %s not found in config' %  (str(e)))
            acquisition = self.assemble_acquisition()
            display = self.assemble_display()
            channel = self.assemble_channel()
            trigger = self.assemble_trigger()
            cfg = self.assemble_config()
            
        # line up in order
        paramcfg = [acquisition, trigger, display, cfg]
        for ch in channel:
            paramcfg.append(ch)
        statistics = self.assemble_statistics()
        
        paramcfg.append(statistics)

        return paramcfg
