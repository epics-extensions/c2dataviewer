# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2020 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Unit tests for Imagev

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""
import os
import sys
import unittest
import numpy as np
import pvaccess as pva
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt import QtCore, QtTest
from .helper import create_image
from .helper import setup_qt_app

from c2dataviewer.view.image_definitions import *
from c2dataviewer.imagev import ImageWindow
from c2dataviewer.view.image_display import ImagePlotWidget

os.environ["QT_QPA_PLATFORM"] = "offscreen"
        
############################################
# Test
############################################
class TestImageDisplay(unittest.TestCase):

    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.

        :return:
        """
        # Create Qt application
        setup_qt_app()
         
        # Create ImageWindow and get the imageWidget instance
        self.window = ImageWindow()
        self.imageWidget = self.window.imageWidget
        self.imageWidget.resize(1000,1000)
        self.imageWidget.use_embeddedDataLen = False

        # GUI styles
        self._inputTypeDefaultStyle = self.window.tbValidInput.styleSheet()

    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """

############################################
# Test datatypes (display method)
############################################

    def runDatatypeSupportTest(self, dataType, xDim, yDim, arrayValue, inputValid = True):
        """
        Check if ImagePlotWidget class can handle specified datatype

        """

        types = {
            pva.BYTE : {'string' : 'byteValue', 'min': np.iinfo(np.int8).min, 'max' : np.iinfo(np.int8).max},
            pva.UBYTE : {'string' : 'ubyteValue', 'min': np.iinfo(np.uint8).min, 'max' : np.iinfo(np.uint8).max},

            pva.SHORT : {'string' : 'shortValue', 'min': np.iinfo(np.int16).min, 'max' : np.iinfo(np.int16).max},
            pva.USHORT : {'string' : 'ushortValue', 'min': np.iinfo(np.uint16).min, 'max' : np.iinfo(np.uint16).max},

            pva.INT : {'string' : 'intValue', 'min': np.iinfo(np.int32).min, 'max' : np.iinfo(np.int32).max},
            pva.UINT : {'string' : 'uintValue', 'min': np.iinfo(np.uint32).min, 'max' : np.iinfo(np.uint32).max},

            pva.LONG : {'string' : 'longValue', 'min': np.iinfo(np.int64).min, 'max' : np.iinfo(np.int64).max},
            pva.ULONG : {'string' : 'ulongValue', 'min': np.iinfo(np.uint32).min, 'max' : np.iinfo(np.uint32).max},

            pva.FLOAT : {'string' : 'floatValue', 'min': np.finfo(np.float32).min, 'max' : np.finfo(np.float32).max},
            pva.DOUBLE : {'string' : 'doubleValue', 'min': np.finfo(np.float64).min, 'max' : np.finfo(np.float64).max},
        }

        data = create_image(1, arrayValue, types[dataType]['string'], nx=xDim, ny=yDim, color_mode=0, extra_fields_PV_object={types[dataType]['string'] : [dataType]})

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

        self.runDatatypeSupportTest(pva.UBYTE, x, y, arrayValue)


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

        self.runDatatypeSupportTest(pva.SHORT, x, y, arrayValue)


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

        self.runDatatypeSupportTest(pva.USHORT, x, y, arrayValue)


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

        self.runDatatypeSupportTest(pva.INT, x, y, arrayValue)


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

        self.runDatatypeSupportTest(pva.UINT, x, y, arrayValue)


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

        self.runDatatypeSupportTest(pva.FLOAT, x, y, arrayValue)


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

        self.runDatatypeSupportTest(pva.DOUBLE, x, y, arrayValue)

############################################
# Test zoom capability
############################################

    def test_zoom(self):
        
        """

        """
        # Build test image
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

        data = create_image(1, arrayValue, nx=10, ny=10, color_mode=0)

        # Display original image
        self.imageWidget.display(data)

        # Test zoom parameters
        xOffset, yOffset, width, height = self.imageWidget.get_zoom_region()
        self.assertFalse(self.imageWidget.is_zoomed())
        self.assertEqual(0, xOffset)
        self.assertEqual(0, yOffset)
        self.assertEqual(10, width)
        self.assertEqual(10, height)

        # Change ROI programmatically
        self.imageWidget._ImagePlotWidget__calculateZoomParameters(100, 500, 100, 500)

        # Test zoom dist values
        xOffset, yOffset, width, height = self.imageWidget.get_zoom_region()
        self.assertTrue(self.imageWidget.is_zoomed())
        self.assertEqual(1, xOffset)
        self.assertEqual(1, yOffset)
        self.assertEqual(4, width)
        self.assertEqual(4, height)

        # Call reset zoom programmatically as we do not have the button available here
        self.imageWidget.reset_zoom()
        xOffset, yOffset, width, height = self.imageWidget.get_zoom_region()
        self.assertFalse(self.imageWidget.is_zoomed())
        self.assertEqual(0, xOffset)
        self.assertEqual(0, yOffset)
        self.assertEqual(10, width)
        self.assertEqual(10, height)

        
        # Select roi by simulating mouse clicks
        # The mouseRelease causes the imageWidget to resize to 562x562, causing the resulting
        # width to be 7.  Disable this test until reason behind behavior is understood
        #
        # QtTest.QTest.mousePress(self.imageWidget, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
        #                     QtCore.QPoint(500, 500), -1)
        # QtTest.QTest.mouseRelease(self.imageWidget, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
        #                     QtCore.QPoint(100, 100), 500)

        # # Test if roi was zoomed
        # xOffset, yOffset, width, height = self.imageWidget.get_zoom_region()
        # self.assertTrue(self.imageWidget.is_zoomed())
        # self.assertEqual(1, xOffset)
        # self.assertEqual(1, yOffset)
        # self.assertEqual(7, width)
        # self.assertEqual(7, height)
        # self.imageWidget.reset_zoom()

        # Try to select outside the image (Check if the zoom is ignored if user click outside the widget)
        QtTest.QTest.mousePress(self.imageWidget, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
                            QtCore.QPoint(2000, 2000), -1)
        QtTest.QTest.mouseRelease(self.imageWidget, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier,
                            QtCore.QPoint(250, 200), 50)

        # Assure that image was not zoomed
        xOffset, yOffset, width, height = self.imageWidget.get_zoom_region()
        self.assertFalse(self.imageWidget.is_zoomed())
        self.assertEqual(0, xOffset)
        self.assertEqual(0, yOffset)
        self.assertEqual(10, width)
        self.assertEqual(10, height)

    def test_no_color_mode(self):
        #Make sure that can process mono images even though they don't have a color mode
        image = create_image(1, nx=8, ny=8)
        try:
            self.imageWidget.display(image)
        except RuntimeError as e:
            self.assertTrue(False, e)
