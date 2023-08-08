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
import unittest.mock as mock
from pvaccess import PvObject
from pvaccess import NtNdArray
import pvaccess as pva
import numpy as np
from pyqtgraph.Qt import QtWidgets
from pyqtgraph import QtCore

from c2dataviewer.imagev import ImageSettingsDialog, WarningDialog
from c2dataviewer.imagev import ImageController
from c2dataviewer.imagev import ImageWindow

from .helper import create_image
from .helper import setup_qt_app

os.environ["QT_QPA_PLATFORM"] = "offscreen"

class TestImageDisplay(unittest.TestCase):

    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.

        :return:
        """

        # Create Qt application
        setup_qt_app()
        
        # Create ImageWindow and het the imageWidget instance
        self.window = ImageWindow()
        self.imageWidget = self.window.imageWidget

        # Build GUI elements
        w = ImageWindow(None)
        datasource = mock.Mock()
        w.imageWidget.set_datasource(datasource)
        image_settings_dialog = ImageSettingsDialog(None)
        warning = WarningDialog(None)

        self.ic = ImageController(w, IMAGE_SETTINGS_DIALOG=image_settings_dialog, WARNING=warning,
                PV={'test', 'test'}, timer=QtCore.QTimer(), data=None)

    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """

    def test_blackSetting(self):
        """
        Test if setting black value behaves correctly

        :return:
        """

        # Test default values
        self.assertEqual(0, self.ic._win.imageBlackSlider.value())
        self.assertEqual(0, self.ic._win.imageBlackSlider.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageBlackSlider.maximum())
        self.assertEqual(0, self.ic._win.imageBlackSpinBox.value())
        self.assertEqual(0, self.ic._win.imageBlackSpinBox.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageBlackSpinBox.maximum())


        # Set black to 100
        self.ic.updateGuiBlack(100)
        self.assertEqual(100, self.ic._win.imageBlackSlider.value())
        self.assertEqual(0, self.ic._win.imageBlackSlider.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageBlackSlider.maximum())
        self.assertEqual(100, self.ic._win.imageBlackSpinBox.value())
        self.assertEqual(0, self.ic._win.imageBlackSpinBox.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageBlackSpinBox.maximum())

        # Set limits
        self.ic.changeimageBlackLimits(-10, 50)
        self.assertEqual(50, self.ic._win.imageBlackSlider.value())
        self.assertEqual(-10, self.ic._win.imageBlackSlider.minimum())
        self.assertEqual(50, self.ic._win.imageBlackSlider.maximum())
        self.assertEqual(50, self.ic._win.imageBlackSpinBox.value())
        self.assertEqual(-10, self.ic._win.imageBlackSpinBox.minimum())
        self.assertEqual(50, self.ic._win.imageBlackSpinBox.maximum())

        # Set limits bigger than slider allows (test factor implementation)
        self.ic.changeimageBlackLimits(0, self.ic.SLIDER_MAX_VAL * 2)
        self.ic.updateGuiBlack(self.ic.SLIDER_MAX_VAL * 1.5)
        self.assertAlmostEqual(self.ic.SLIDER_MAX_VAL * 1.5, self.ic._win.imageBlackSlider.value() / self.ic._imageBlackSliderFactor, delta=1)
        self.assertEqual(0, self.ic._win.imageBlackSlider.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageBlackSlider.maximum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL * 1.5, self.ic._win.imageBlackSpinBox.value())
        self.assertEqual(0, self.ic._win.imageBlackSpinBox.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL * 2, self.ic._win.imageBlackSpinBox.maximum())

    def test_whiteSetting(self):
        """
        Test if setting white value behaves correctly

        :return:
        """

        # Test default values
        self.assertEqual(1, self.ic._win.imageWhiteSlider.value())
        self.assertEqual(1, self.ic._win.imageWhiteSlider.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageWhiteSlider.maximum())
        self.assertEqual(1, self.ic._win.imageWhiteSpinBox.value())
        self.assertEqual(1, self.ic._win.imageWhiteSpinBox.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageWhiteSpinBox.maximum())


        # Set White to 100
        self.ic.updateGuiWhite(100)
        self.assertEqual(100, self.ic._win.imageWhiteSlider.value())
        self.assertEqual(1, self.ic._win.imageWhiteSlider.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageWhiteSlider.maximum())
        self.assertEqual(100, self.ic._win.imageWhiteSpinBox.value())
        self.assertEqual(1, self.ic._win.imageWhiteSpinBox.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageWhiteSpinBox.maximum())

        # Set limits
        self.ic.changeimageWhiteLimits(-10, 50)
        self.assertEqual(50, self.ic._win.imageWhiteSlider.value())
        self.assertEqual(-10, self.ic._win.imageWhiteSlider.minimum())
        self.assertEqual(50, self.ic._win.imageWhiteSlider.maximum())
        self.assertEqual(50, self.ic._win.imageWhiteSpinBox.value())
        self.assertEqual(-10, self.ic._win.imageWhiteSpinBox.minimum())
        self.assertEqual(50, self.ic._win.imageWhiteSpinBox.maximum())

        # Set limits bigger than slider allows (test factor implementation)
        self.ic.changeimageWhiteLimits(0, self.ic.SLIDER_MAX_VAL * 2)
        self.ic.updateGuiWhite(self.ic.SLIDER_MAX_VAL * 1.5)
        self.assertAlmostEqual(self.ic.SLIDER_MAX_VAL * 1.5, self.ic._win.imageWhiteSlider.value() / self.ic._imageWhiteSliderFactor, delta=1)
        self.assertEqual(0, self.ic._win.imageWhiteSlider.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL, self.ic._win.imageWhiteSlider.maximum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL * 1.5, self.ic._win.imageWhiteSpinBox.value())
        self.assertEqual(0, self.ic._win.imageWhiteSpinBox.minimum())
        self.assertEqual(self.ic.SLIDER_MAX_VAL * 2, self.ic._win.imageWhiteSpinBox.maximum())

    def test_zoomInformation(self):
        """
        Test if zoom information is properly displayed on the GUI

        :return:
        """

        # Setup image inside the ImagePlotWidget
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
        self.ic._win.imageWidget._ImagePlotWidget__update_dimension(data)
        self.ic._win.imageWidget.display(data)
        self.ic._win.imageWidget.data = data

        # Update the GUI
        self.ic.updateStatus()

        # Check the information on the gui
        self.assertEqual("10", self.ic._win.lblXsize.text().strip())
        self.assertEqual("10", self.ic._win.lblYsize.text().strip())
        self.assertEqual("0", self.ic._win.deadPixel.text().strip())
        self.assertEqual("255.0", self.ic._win.maxPixel.text().strip())
        self.assertEqual("0.0", self.ic._win.minPixel.text().strip())

        # Set zoom region
        self.ic._win.imageWidget.set_zoom_region(4, 3, 5, 8)

        # Update the GUI
        self.ic.updateStatus()

        # Check the information on the gui
        self.assertEqual("10 (5|4-9)", self.ic._win.lblXsize.text().strip())
        self.assertEqual("10 (7|3-10)", self.ic._win.lblYsize.text().strip())
        self.assertEqual("0 (0)", self.ic._win.deadPixel.text().strip())
        self.assertEqual("255.0 (76.0)", self.ic._win.maxPixel.text().strip())
        self.assertEqual("0.0 (23.0)", self.ic._win.minPixel.text().strip())

        # Reset zoom
        self.ic._win.imageWidget.reset_zoom()

        # Update the GUI
        self.ic.updateStatus()

        # Check the information on the gui
        self.assertEqual("10", self.ic._win.lblXsize.text().strip())
        self.assertEqual("10", self.ic._win.lblYsize.text().strip())
        self.assertEqual("0", self.ic._win.deadPixel.text().strip())
        self.assertEqual("255.0", self.ic._win.maxPixel.text().strip())
        self.assertEqual("0.0", self.ic._win.minPixel.text().strip())



############################################
# Test statistics
############################################

    def test_statistics(self):
        """
        Test statistics calculations.

        :return:
        """
        # Constants
        NX = 10
        NY = 10
        COLOR_MODE = 0
        N_IMAGES = 20 # For each rate

        # Build image
        self.imageWidget.x = NX
        self.imageWidget.y = NY

        # Generate images
        array_value = [
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
        np_value = np.array(array_value, dtype=np.uint8)
        image_counter = 0

        # Calculate init statistics
        self.ic.calculate_statistics()
        self.assertAlmostEqual(0.0, self.ic._win.imageWidget.MB_received, delta=0.0001)
        self.assertEqual(0, self.ic._win.imageWidget.frames_displayed)
        self.assertAlmostEqual(0, self.ic.fps_current, delta=0.1)
        self.assertAlmostEqual(0, self.ic.fps_average, delta=0.1)
        self.assertAlmostEqual(0, self.ic.fps_current_received, delta=0.1)
        self.assertAlmostEqual(0, self.ic.fps_average_received, delta=0.1)
        self.assertEqual(0, self.ic.frames_missed_current)
        self.assertAlmostEqual(0.0, self.ic.frames_missed_average, delta=0.5)
        self.assertEqual(0, self.ic._win.imageWidget.frames_missed)
        self.assertEqual(0, self.ic._win.imageWidget.minVal)
        self.assertEqual(0, self.ic._win.imageWidget.maxVal)

        # Generate images
        for i in range(N_IMAGES):
            image_counter += 1
            if i % 3 == 0:
                continue
            image = create_image(image_counter, np_value, nx=NX, ny=NY, color_mode=COLOR_MODE,  time_stamp=image_counter)
            self.ic._win.imageWidget._ImagePlotWidget__update_dimension(image)
            self.ic._win.imageWidget.display(image)

        # Calculate statistics
        self.ic.calculate_statistics()
        self.assertAlmostEqual(0.0012, self.ic._win.imageWidget.MB_received, delta=0.0001)
        self.assertEqual(12, self.ic._win.imageWidget.frames_displayed)
        self.assertEqual(7, self.ic._win.imageWidget.frames_missed)
        self.assertEqual(min(array_value), self.ic._win.imageWidget.minVal)
        self.assertEqual(max(array_value), self.ic._win.imageWidget.maxVal)

        # Generate images
        for i in range(N_IMAGES):
            image_counter += 1
            if i % 3 == 0:
                continue
            image = create_image(image_counter, np_value, nx=10, ny=10, color_mode=0,  time_stamp=image_counter)
            self.ic._win.imageWidget._ImagePlotWidget__update_dimension(image)
            self.ic._win.imageWidget.display(image)

        # Calculate statistics
        self.ic.calculate_statistics()
        self.assertAlmostEqual(0.0025, self.ic._win.imageWidget.MB_received, delta=0.0001)
        self.assertEqual(25, self.ic._win.imageWidget.frames_displayed)
        self.assertEqual(14, self.ic._win.imageWidget.frames_missed)
        self.assertEqual(min(array_value), self.ic._win.imageWidget.minVal)
        self.assertEqual(max(array_value), self.ic._win.imageWidget.maxVal)

        # Generate images
        for i in range(N_IMAGES):
            image_counter += 1
            if i % 3 == 0:
                continue
            image = create_image(image_counter, np_value, nx=10, ny=10, color_mode=0,  time_stamp=image_counter)
            self.ic._win.imageWidget._ImagePlotWidget__update_dimension(image)
            self.ic._win.imageWidget.display(image)

        # Calculate statistics
        self.ic.calculate_statistics()
        self.assertAlmostEqual(0.0038, self.ic._win.imageWidget.MB_received, delta=0.0001)
        self.assertEqual(38, self.ic._win.imageWidget.frames_displayed)
        self.assertEqual(21, self.ic._win.imageWidget.frames_missed)
        self.assertEqual(min(array_value), self.ic._win.imageWidget.minVal)
        self.assertEqual(max(array_value), self.ic._win.imageWidget.maxVal)
