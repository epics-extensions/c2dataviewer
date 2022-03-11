import unittest
import os
import sys

from configparser import ConfigParser
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.parametertree import Parameter

from c2dataviewer.model import DataSource as DataReceiver
from c2dataviewer.view import StripToolConfigure
from c2dataviewer.striptool import StripToolWindow, WarningDialog, PvEditDialog

from c2dataviewer.control.striptool_config import StriptoolConfig
from c2dataviewer.control.striptool_controller import StripToolController
from c2dataviewer.control.pvconfig import PvConfig

os.environ["QT_QPA_PLATFORM"] = "offscreen"

class TestStriptoolController(unittest.TestCase):
    def setUp(self):
        # Create Qt application
        self.app = QtWidgets.QApplication(sys.argv)

        # Create ImageWindow and get the imageWidget instance
        self.window = StripToolWindow()

        # Build parameter tree
        cf = ConfigParser()
        configure = StripToolConfigure(cf)
        self.parameters = Parameter.create(
            name="params", type="group", children=configure.parse())
        self.window.parameterPane.setParameters(self.parameters, showTop=False)

        # Model to be used
        self.model = DataReceiver()

        # Build GUI elements
        self.warning = WarningDialog(None)
        
        raw = """
[STRIPTOOL]
Chan1.PV = pva://Bar:Baz
Chan2.PV = pva://Bar:Baz2
Chan1.Color = #000000
Chan2.Color = #FFFFFF
        """
        cfg = ConfigParser()
        cfg.read_string(raw)
        self.cfg = cfg

        self.pvedit_dialog = PvEditDialog()
        
        self.scope_controller = StripToolController(
            self.window,  self.model, self.pvedit_dialog, self.warning, self.parameters, self.cfg)

    
    def test_pvlist(self):
        expected = {
            'Bar:Baz' : PvConfig('Bar:Baz', '#000000', 'pva'),
            'Bar:Baz2' : PvConfig('Bar:Baz2', '#FFFFFF', 'pva'),
            }
        pvdict = self.scope_controller.pvdict
        self.assertEqual(len(expected), len(pvdict))
        for k, v in expected.items():
            self.assertTrue(k in pvdict)
            p = pvdict[k].make_pvconfig()
            self.assertEqual(p.pvname, v.pvname)
            self.assertEqual(p.color, v.color)
            self.assertEqual(p.proto, v.proto)


        newpvlist = [ PvConfig('Foo:bar', '#444444', 'ca'), PvConfig('Foo:bar2', '#555555', 'ca') ]
        self.scope_controller.pv_edit_callback(newpvlist)
        self.assertEqual(len(newpvlist), len(pvdict))
        pvdict = self.scope_controller.pvdict
        for v in newpvlist:
            self.assertTrue(v.pvname in pvdict)
            p = pvdict[v.pvname].make_pvconfig()
            self.assertEqual(p.pvname, v.pvname)
            self.assertEqual(p.color, v.color)
            self.assertEqual(p.proto, v.proto)
            
        

