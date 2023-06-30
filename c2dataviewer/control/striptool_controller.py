"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

import logging
import pyqtgraph
from  .pvedit_dialog_controller import PvEditDialogController
import random
from PyQt5 import QtGui
from ..model import ConnectionState
import pvaccess as pva
from ..view import *
from .scope_controller_base import ScopeControllerBase
from ..view.scope_display import PlotChannel as ScopePlotChannel
from pyqtgraph.parametertree import Parameter
from .striptool_config import StriptoolConfig
from .pvconfig import PvConfig

class PvScopeItem:
    def __init__(self, props, controller):
        self.pvname = props.pvname
        self.proto = props.proto
        self.channel = ScopePlotChannel(props.pvname, props.color)
        self.parent_controller = controller
        self.connection = controller.model.create_connection(props.pvname, provider=props.proto)        
        self.status =  str(self.connection.state)
        self.hide = False

    def start(self):
        if not self.connection.is_running():
            self.connection.start(status_callback=self.connection_changed_callback,
                                  routine=self.monitor_callback)

    def set_hide(self, val):
        self.hide = val
        if not val:
            self.channel.pvname = self.pvname
        else:
            self.channel.pvname = 'None'
            
    def stop(self):
        self.connection.stop()
        self.parent_controller._win.graphicsWidget.clear_sample_data(self.pvname)

    def update_properties(self, props):
        self.channel.color = props.color
        if self.proto != props.proto:
            self.stop()
            self.proto = props.proto
            self.connection = self.parent_controller.model.create_connection(self.pvname, provider=self.proto)
            self.connection_changed_callback(self.connection.state, None)
            self.start()
            
    def connection_changed_callback(self, state, msg):
        status = str(state)
        if msg:
            status += ': ' + msg
            
        self.status = status

        if not self.connection.is_running():
            self.parent_controller._win.graphicsWidget.clear_sample_data(self.pvname)
            
        self.parent_controller.update_channel_param(self.pvname, "Proto/status",
                                                    "%s/%s" % (str(self.proto), status))
        
    def monitor_callback(self, data):
        try:
            data =  data['value']
        except:
            logging.getLogger().error('Unable to plot %s. PV is not scalar. Stopping connection', self.pvname)
            self.stop()
            return

        self.parent_controller.data_callback(self.pvname, data)

    def __del__(self):
        self.connection.stop()

    def make_pvconfig(self):
        return PvConfig(self.pvname, self.channel.color, self.proto)
    

class StripToolController(ScopeControllerBase):
    def __init__(self, widget, model, pvedit_widget, warning, parameters,
                 cfg,
                 **kwargs):

        super().__init__(widget, model, parameters, warning, **kwargs)
        st_config = StriptoolConfig(cfg, **kwargs)
        self._pvedit_dialog = PvEditDialogController(pvedit_widget, model,
                                                     default_proto=st_config.default_proto)
        self._win.editPvButton.clicked.connect(self._on_pvedit_click)
        self.default_config(**kwargs)
        #default to showing 60 second of data
        if not self._win.graphicsWidget.max_length:
            self.update_buffer_samples(int(60000 / self.refresh))

        self._win.graphicsWidget.enable_sampling_mode(True)
        self._win.graphicsWidget.set_autoscale(parameters.child('Display', 'Autoscale').value())
        self._pvedit_dialog.set_completion_callback(self.pv_edit_callback)
        self._init_pvlist(st_config.pvs.values())

        self.start_plotting()
        
    def _init_pvlist(self, pvconfig):
        self.pvdict = {}
        pvlist = []
        for p in pvconfig:
            if not p.pvname:
                continue
            
            pvlist.append(p)
        self._set_pv_list(pvlist)
        
    def _on_pvedit_click(self):
        pvlist = []
        for p in self.pvdict.values():
            cfg = p.make_pvconfig()
            pvlist.append(cfg)
            
        self._pvedit_dialog.show(pvlist)

    def pv_edit_callback(self, newpvlist):
        self._set_pv_list(newpvlist)

    def _set_pv_list(self, pvlist):
        oldpvnames_set = set(self.pvdict.keys())
        newpvnames_set = set([p.pvname for p in pvlist])

        newpvs = newpvnames_set - oldpvnames_set
        removed_pvs = oldpvnames_set - newpvnames_set
        
        #remove pvs
        for p in removed_pvs:
            item = self.pvdict[p]
            del self.pvdict[p]
            
        #new pvs        
        for p in pvlist:
            pvname = p.pvname
            if pvname not in self.pvdict:
                si =  PvScopeItem(p, self)
                self.pvdict[pvname] = si
            else:
                si = self.pvdict[pvname]
                si.update_properties(p)
        
        #setup channel config
        self._setup_channel_config()
        
        #create channel list
        self._setup_plot()
        
        for si in self.pvdict.values():
            si.start()
            
            
    def _setup_plot(self):
        channels = [ si.channel for si in self.pvdict.values() ]
        self._win.graphicsWidget.setup_plot(channels)
        
    def _setup_channel_config(self):
        channel = []
        for si in self.pvdict.values():
            channel.append(
                { "name" : si.pvname,
                  "type": "group",
                  "children": [
                      {"name": "Proto/status", "type": "str",
                       "value": "%s/%s" % (str(si.proto), si.status),
                       "readonly":True},
                      {"name": "Hide", "type": "bool", "value":si.hide},
                      {
                          "name": "Color",
                          "type": "color",
                          "value": si.channel.color
                      },
                      {"name": "DC offset", "type": "float", "value": si.channel.dc_offset},
                      {"name": "Axis location", "type": "list", "values": {
                          "Left" : "left",
                          "Right" : "right",
                      }, "value" : si.channel.axis_location},
                  ]
                })
        parameters = Parameter.create(name="params", type="group", children=channel)
        parameters.sigTreeStateChanged.connect(self.channel_param_changed)
        self.chan_parameters = parameters
        self._win.channelParamPane.setParameters(parameters, showTop=False)

    def update_channel_param(self, pvname, pname, val):
        param = self.chan_parameters.child(pvname).child(pname)
        param.setValue(val)
        
    def data_callback(self, pvname, data):
        def generator():
            d = {pvname: data}
            
            for k, v in d.items():
                yield k, v
            
        self._win.graphicsWidget.data_process(generator)
        
    def channel_param_changed(self, params, changes):
        for param, change, data, in changes:
            if change != "value":
                continue
            
            child = self.chan_parameters.childPath(param)
            if not child:
                continue
            
            pvname = child[0]
            si = self.pvdict[pvname]
            
            pname = param.name()
            if pname == 'Hide':
                si.set_hide(data)
            elif pname == 'Color':
                c = data.getRgb()
                si.channel.color = '#%02x%02x%02x' % (c[0], c[1], c[2])
            elif pname == 'DC offset':
                si.channel.dc_offset = data
            elif pname == 'Axis location':
                si.channel.axis_location = data

        self._setup_plot()

    def set_sampling_mode(self, val):
        self._win.graphicsWidget.enable_sampling_mode(val)
        
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

                if childName == "Acquisition.Sample Mode":
                    self.set_sampling_mode(data)
                    
        super().parameter_change(params, changes)
