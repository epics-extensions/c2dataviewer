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
        try:
            autoscale = self.params["STRIPTOOL"]["AUTOSCALE"]
        except KeyError:
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


