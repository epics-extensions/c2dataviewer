# -*- coding: utf-8 -*-

"""
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

        # Create Qt application
        self.app = QtWidgets.QApplication(sys.argv)

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
        self.app.quit()

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
