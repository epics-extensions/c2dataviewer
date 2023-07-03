"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

from .scope_config_base import ScopeConfigureBase

class StripToolConfigure(ScopeConfigureBase):
    def __init__(self, params, **kwargs):
        super().__init__(params, **kwargs)

    def assemble_acquisition(self, section=None):
        acquisition = super().assemble_acquisition(section)
        children = acquisition['children']

        children.append({"name": "Sample Mode", "type":"bool", "value": True})

        return acquisition
    
    def assemble_display(self, section=None):
        # If AUTOSCALE set in the app specific sections in the config file
        try:
            autoscale = self.params["STRIPTOOL"]["AUTOSCALE"] or None
        except KeyError:
            autoscale = None

        if autoscale is None:
            # Else if AUTOSCALE set in the DISPLAY specific section in the config file
            try:
                autoscale = self.params["DISPLAY"]["AUTOSCALE"] or None
            except KeyError:
                autoscale = None
        
        # If AUTOSCALE not set anywhere in the config file, set default value
        if autoscale is None:
            autoscale = True
        
        display = super().assemble_display(section, autoscale=autoscale)

        return display
    
    def parse(self):
        try:
            acquisition = self.assemble_acquisition(self.params["ACQUISITION"])
        except KeyError:
            acquisition = self.assemble_acquisition()

        try:
            display = self.assemble_display(self.params["DISPLAY"])
        except KeyError:
            display = self.assemble_display()
            
        statistics = self.assemble_statistics()
        # line up in order
        paramcfg = [acquisition, display, statistics]

        return paramcfg


