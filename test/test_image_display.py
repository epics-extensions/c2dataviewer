# -*- coding: utf-8 -*-

"""
Copyright 2020 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Unit tests for Imagev

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""
import os
import sys
import unittest
from pvaccess import PvObject
from pvaccess import NtNdArray
from pvaccess import PvDimension
from pvaccess import BYTE, UBYTE, SHORT, USHORT, INT, UINT, LONG, ULONG, FLOAT, DOUBLE
import numpy as np
from pyqtgraph.Qt import QtWidgets

from c2dataviewer.imagev import ImageWindow

os.environ["QT_QPA_PLATFORM"] = "offscreen"

class TestImageDisplay(unittest.TestCase):

    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.

        :return:
        """
        # Create Qt application
        self.app = QtWidgets.QApplication(sys.argv)

        # Create ImageWindow and het the imageWidget instance
        self.window = ImageWindow()
        self.imageWidget = self.window.imageWidget

        # GUI styles
        self._inputTypeDefaultStyle = self.window.lblValidInput.styleSheet()

    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """
        self.app.quit()

############################################
# Test datatypes (display method)
############################################


    def runDatatypeSupportTest(self, dataType, xDim, yDim, arrayValue, inputValid = True):
        """
        Check if ImagePlotWidget class can handle specified datatype

        """

        types = {
            BYTE : {'string' : 'byteValue', 'min': np.iinfo(np.int8).min, 'max' : np.iinfo(np.int8).max},
            UBYTE : {'string' : 'ubyteValue', 'min': np.iinfo(np.uint8).min, 'max' : np.iinfo(np.uint8).max},

            SHORT : {'string' : 'shortValue', 'min': np.iinfo(np.int16).min, 'max' : np.iinfo(np.int16).max},
            USHORT : {'string' : 'ushortValue', 'min': np.iinfo(np.uint16).min, 'max' : np.iinfo(np.uint16).max},

            INT : {'string' : 'intValue', 'min': np.iinfo(np.int32).min, 'max' : np.iinfo(np.int32).max},
            UINT : {'string' : 'uintValue', 'min': np.iinfo(np.uint32).min, 'max' : np.iinfo(np.uint32).max},

            LONG : {'string' : 'longValue', 'min': np.iinfo(np.int64).min, 'max' : np.iinfo(np.int64).max},
            ULONG : {'string' : 'ulongValue', 'min': np.iinfo(np.uint32).min, 'max' : np.iinfo(np.uint32).max},

            FLOAT : {'string' : 'floatValue', 'min': np.finfo(np.float32).min, 'max' : np.finfo(np.float32).max},
            DOUBLE : {'string' : 'doubleValue', 'min': np.finfo(np.float64).min, 'max' : np.finfo(np.float64).max},
        }

        data = NtNdArray()
        data.setValue(PvObject({types[dataType]['string'] : [dataType]},
                               {types[dataType]['string'] : arrayValue},
                     ))

        self.imageWidget.x = xDim
        self.imageWidget.y = yDim
        self.assertEqual(self.imageWidget.x * self.imageWidget.y,
                            data.getValue()[types[dataType]['string']].size,
                            "Size of the array does not match its dimensions")


        if inputValid:
            try:
                self.imageWidget.display(data)
            except RuntimeError:
                self.assertTrue(False, "ImagePlotWidget:display() throw RuntimeError for valid input")
            self.assertTrue(self.imageWidget._isInputValid)
        else:
            self.assertRaises(RuntimeError, self.imageWidget.display, data)
            self.assertFalse(self.imageWidget._isInputValid)


    def test_Int8DataTypeSupport(self):
        """
        Check if ImagePlotWidget class can handle Int8 data type.
        """

        x = 10
        y = 10

        arrayValue = [
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            127, -128, 77, -54, -23, 76, -34, 65, -34, 65,
            ]

        # self.runDatatypeSupportTest(BYTE, x, y, arrayValue)


    def test_UInt8DataTypeSupport(self):
        """
        Check if ImagePlotWidget class can handle UInt8 data type.
        """

        x = 10
        y = 10

        arrayValue = [
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            255, 0, 77, 54, 23, 76, 34, 65, 34, 65,
            ]

        self.runDatatypeSupportTest(UBYTE, x, y, arrayValue)


    def test_Int16DataTypeSupport(self):
        """
        Check if ImagePlotWidget class can handle Int16 data type.
        """

        x = 10
        y = 10

        arrayValue = [
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            32767, -32768, 25123, -7415, 745, 7412, 6524, -29147, 4523, 65,
            ]

        self.runDatatypeSupportTest(SHORT, x, y, arrayValue)


    def test_UInt16DataTypeSupport(self):
        """
        Check if ImagePlotWidget class can handle UInt16 data type.
        """

        x = 10
        y = 10

        arrayValue = [
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            65535, 0, 54123, 7415, 745, 7412, 6524, 52147, 4523, 65,
            ]

        self.runDatatypeSupportTest(USHORT, x, y, arrayValue)


    def test_Int32DataTypeSupport(self):
        """
        Check if ImagePlotWidget class can handle Int32 data type.
        """

        x = 10
        y = 10

        arrayValue = [
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            2147483647, -2147483648, 214743647, -247483648, 9467295, -4295, 84967295, -10000, 5236222, 65,
            ]

        self.runDatatypeSupportTest(INT, x, y, arrayValue)


    def test_UInt32DataTypeSupport(self):
        """
        Check if ImagePlotWidget class can handle UInt32 data type.
        """

        x = 10
        y = 10

        arrayValue = [
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            4294967295, 0, 429497295, 429492395, 94967295, 4295, 84967295, 10000, 5236222, 65,
            ]

        self.runDatatypeSupportTest(UINT, x, y, arrayValue)


    def test_Float32DataTypeSupport(self):
        """
        Check if ImagePlotWidget class can handle Float32 data type.
        """

        x = 10
        y = 10

        arrayValue = [
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            125411.1245, 0, 12455214, 5454545, 12547896.14587, 74569698, 785.25114456, 142144444, 7575775, 7575.111111,
            ]

        self.runDatatypeSupportTest(FLOAT, x, y, arrayValue)


    def test_Float64DataTypeSupport(self):
        """
        Check if ImagePlotWidget class can handle Float64 data type.
        """

        x = 10
        y = 10

        arrayValue = [
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            32125411.1245, -32125411.1245, 12455214, 5454545, -12547896.14587, 74569698, -785.25114456, 142144444, -7575775, 7575.111111,
            ]

        self.runDatatypeSupportTest(DOUBLE, x, y, arrayValue)
