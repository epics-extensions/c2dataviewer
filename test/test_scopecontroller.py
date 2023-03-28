# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2021 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Unit tests for Scope controller

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""
import os
import sys
import unittest
import configparser
import pvaccess as pva

from pyqtgraph.Qt import QtWidgets
from pyqtgraph.parametertree import Parameter

from c2dataviewer.model import DataSource as DataReceiver
from c2dataviewer.view import Configure
from c2dataviewer.scope import ScopeWindow, WarningDialog
from c2dataviewer.control import ScopeController


os.environ["QT_QPA_PLATFORM"] = "offscreen"


class TestImageDisplay(unittest.TestCase):
    """
    Units tests for the scope controllers.
    """

    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.

        :return:
        """

        # Create ImageWindow and get the imageWidget instance
        self.window = ScopeWindow()

        # Build parameter tree
        configure = Configure(configparser.ConfigParser())
        parameters = Parameter.create(
            name="params", type="group", children=configure.parse())
        self.window.parameterPane.setParameters(parameters, showTop=False)

        # Model to be used
        model = DataReceiver()

        # Build GUI elements
        warning = WarningDialog(None)

        self.scope_controller = ScopeController(
            widget=self.window, model=model, parameters=parameters, WARNING=warning)

    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """
        pass

    def test_update_status(self):
        """
        Test update statistics
        """
        #make sure that update_status runs without errors
        self.scope_controller.update_status()


    def test_get_fdr(self):
        """
        Test if the PV structure is properly parsed and correct fields are
        extracted to be used as a drop down items on the GUI. This are pva.ScalarType
        and arrays of pva.ScalarType.
        """
        # Mock get for the receiver
        def mock_get(*_):

            test_struct = {
                "anInt": pva.INT,
                "aStruct": {
                    "aStruct_aFloat": pva.FLOAT,
                    "aStruct_aDoubleArray": [pva.DOUBLE],
                },
                "aFloatArray": [pva.FLOAT],
                "aStringArray": [pva.STRING],
                "aStructArray": [
                    {
                        "aStructArray_aFloat": pva.FLOAT,
                        "aStructArray_aDoubleArray": [pva.DOUBLE],
                    }
                ],
                "aString": pva.STRING,
                "aDoubleArray": [pva.DOUBLE],
                "aVariant": (),
                "aBooleanArray": [pva.BOOLEAN],
            }
            return pva.PvObject(test_struct)
        self.scope_controller.model.get = mock_get

        fdr, fdr_scalar = self.scope_controller.get_fdr()

        self.assertListEqual(fdr, ['aBooleanArray', 'aDoubleArray',
                             'aFloatArray', 'aStringArray', 'aStruct.aStruct_aDoubleArray'])
        self.assertListEqual(
            fdr_scalar, ['aString', 'aStruct.aStruct_aFloat', 'anInt'])

    def test_buffer_size(self):
        #pass in data
        self.scope_controller.monitor_callback({ 'x' : [10]*100})
        bufval = self.scope_controller.parameters.child("Acquisition").child("Buffer (Samples)").value()
        self.assertEqual(bufval, 100)
        
        #set to object unit
        self.scope_controller.set_buffer_unit('Objects')
        bufval = self.scope_controller.parameters.child("Acquisition").child("Buffer (Objects)").value()
        self.assertEqual(bufval, 1)
        
