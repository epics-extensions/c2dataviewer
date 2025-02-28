"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

import unittest
from configparser import ConfigParser
from c2dataviewer.view.scopeconfig import Configure


class TestScopeConfig(unittest.TestCase):
    def get_display_val(self, data, val):
        for child in data['children']:
            print(child['name'])
            if child['name'] == val:
                ret_val = child['value']
                return ret_val
            
    def test_trigger(self):
        raw1 = """
        [TRIGGER]
        TRIGGER=pv1
        TRIGGER_MODE=onchange
        """
        parser = ConfigParser()
        parser.read_string(raw1)
        configure = Configure(parser)
        section = parser["TRIGGER"]
        self.assertIsNotNone(section)
        trigger = configure.assemble_trigger(section=section)
        self.assertEqual(self.get_display_val(data=trigger, val='PV'), 'pv1')
        self.assertEqual(self.get_display_val(data=trigger, val='Mode'), 'onchange')

    def test_autoscale(self):
        #Does autoscale setting in app specific section take precedence
        raw1 = """
        [SCOPE]
        DefaultProtocol = ca
        AUTOSCALE=False

        [DISPLAY]
        AUTOSCALE=True
        AVERAGE=1
        HISTOGRAM=False
        N_BIN=100
        REFRESH=100
        """
        parser = ConfigParser()
        parser.read_string(raw1)
        configure = Configure(parser)
        section = parser["DISPLAY"]
        display = configure.assemble_display(section=section)

        self.assertFalse(self.get_display_val(data=display, val='Autoscale'))

        #When autoscale setting absent in app specific section, but present in DISPLAY
        raw2 = """
        [SCOPE]
        DefaultProtocol = ca

        [DISPLAY]
        AUTOSCALE=True
        AVERAGE=1
        HISTOGRAM=False
        N_BIN=100
        REFRESH=100
        """
        parser = ConfigParser()
        parser.read_string(raw2)
        configure = Configure(parser)
        section = parser["DISPLAY"]
        display = configure.assemble_display(section=section)
        
        self.assertTrue(self.get_display_val(data=display, val='Autoscale'))

        #When autoscale setting absent in both app specific and in DISPLAY sections,
        #is default selected
        raw3 = """
        [SCOPE]
        DefaultProtocol = ca

        [DISPLAY]
        AVERAGE=1
        HISTOGRAM=False
        N_BIN=100
        REFRESH=100
        """
        parser = ConfigParser()
        parser.read_string(raw3)
        configure = Configure(parser)
        section = parser["DISPLAY"]
        display = configure.assemble_display(section=section)

        self.assertFalse(self.get_display_val(data=display, val='Autoscale'))
