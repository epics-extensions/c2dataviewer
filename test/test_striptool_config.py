"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

import unittest
from configparser import ConfigParser
from c2dataviewer.control.striptool_config import StriptoolConfig
from c2dataviewer.control.pvconfig import PvConfig
from c2dataviewer.view import StripToolConfigure


class TestStriptoolConfig(unittest.TestCase):
    def test_config(self):
        raw = """
[STRIPTOOL]
DefaultProtocol = ca
Chan1.PV = Foo:Bar
Chan2.PV = pva://Bar:Baz
Chan1.Color = #000000
Chan2.Color = #0000FF
"""
        parser = ConfigParser()
        parser.read_string(raw)
        cfg = StriptoolConfig(parser)
        expected = {
            'Foo:Bar': PvConfig('Foo:Bar', '#000000', 'ca'),
            'Bar:Baz': PvConfig('Bar:Baz', '#0000FF', 'pva')
        }

        self.assertEqual(len(cfg.pvs), len(expected))

        for pv in cfg.pvs.values():
            self.assertTrue(pv.pvname in expected)
            e = expected[pv.pvname]
            self.assertEqual(e.pvname, pv.pvname)
            self.assertEqual(e.color, pv.color)
            self.assertEqual(e.proto, pv.proto)
            del expected[pv.pvname]

    def get_display_val(self, data, val):
        for child in data['children']:
            if child['name'] == val:
                ret_val = child['value']
                return ret_val

    def test_autoscale(self):
        #Does autoscale setting in app specific section take precedence
        raw1 = """
        [STRIPTOOL]
        DefaultProtocol = ca
        AUTOSCALE=True

        [DISPLAY]
        AUTOSCALE=False
        AVERAGE=1
        HISTOGRAM=False
        N_BIN=100
        REFRESH=100
        """
        parser = ConfigParser()
        parser.read_string(raw1)
        configure = StripToolConfigure(parser)
        section = parser["DISPLAY"]
        display = configure.assemble_display(section=section)

        self.assertTrue(self.get_display_val(data=display, val='Autoscale'))

        #When autoscale setting absent in app specific section, but present in DISPLAY
        raw2 = """
        [STRIPTOOL]
        DefaultProtocol = ca

        [DISPLAY]
        AUTOSCALE=False
        AVERAGE=1
        HISTOGRAM=False
        N_BIN=100
        REFRESH=100
        """
        parser = ConfigParser()
        parser.read_string(raw2)
        configure = StripToolConfigure(parser)
        section = parser["DISPLAY"]
        display = configure.assemble_display(section=section)
        
        self.assertFalse(self.get_display_val(data=display, val='Autoscale'))

        #When autoscale setting absent in both app specific and in DISPLAY sections,
        #is default selected
        raw3 = """
        [STRIPTOOL]
        DefaultProtocol = ca

        [DISPLAY]
        AVERAGE=1
        HISTOGRAM=False
        N_BIN=100
        REFRESH=100
        """
        parser = ConfigParser()
        parser.read_string(raw3)
        configure = StripToolConfigure(parser)
        section = parser["DISPLAY"]
        display = configure.assemble_display(section=section)

        self.assertTrue(self.get_display_val(data=display, val='Autoscale'))
