"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

import unittest
from configparser import ConfigParser
from c2dataviewer.control.striptool_config import StriptoolConfig
from c2dataviewer.control.pvconfig import PvConfig


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
