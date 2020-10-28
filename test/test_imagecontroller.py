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
from pyqtgraph import QtCore
# from pyqtgraph.Qt import QTest

from c2dataviewer.imagev import LimitDialog, BlackWhiteLimitDialog, WarningDialog
from c2dataviewer.imagev import ImageController
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

        # Build GUI elements
        w = ImageWindow(None)
        dlg = LimitDialog(None)
        blackWhiteDlg = BlackWhiteLimitDialog(None)
        warning = WarningDialog(None)

        self.ic = ImageController(w, LIMIT=dlg, BLACKWHITELIMIT = blackWhiteDlg, WARNING=warning,
                PV={'test', 'test'}, timer=QtCore.QTimer(), data=None)

    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """
        self.app.quit()

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
        data = NtNdArray()
        data.setValue(PvObject({"ubyteValue" : [UBYTE]},
                               {"ubyteValue" : arrayValue},
                     ))


        # Display original image
        # Call __update_dimension directly, as we do not have a datasource we could set here
        # by calling set_datasource, which then updates the dimensions
        dimsData = {}
        dimsData['dimension'] = ({'size' : 10}, {'size' : 10})
        self.ic._win.imageWidget._ImagePlotWidget__update_dimension(dimsData)
        self.ic._win.imageWidget.display(data)
        self.ic._win.imageWidget.data = data

        # Update the GUI
        self.ic.updateStatus()

        # Check the information on the gui
        self.assertEqual("10", self.ic._win.lblXsize.text().strip())
        self.assertEqual("10", self.ic._win.lblYsize.text().strip())
        self.assertEqual("0", self.ic._win.deadPixel.text().strip())
        self.assertEqual("255", self.ic._win.maxPixel.text().strip())
        self.assertEqual("0", self.ic._win.minPixel.text().strip())

        # Set zoom region
        self.ic._win.imageWidget.set_zoom_region(4, 3, 5, 8)

        # Update the GUI
        self.ic.updateStatus()

        # Check the information on the gui
        self.assertEqual("10 (4-9)", self.ic._win.lblXsize.text().strip())
        self.assertEqual("10 (3-10)", self.ic._win.lblYsize.text().strip())
        self.assertEqual("0 (0)", self.ic._win.deadPixel.text().strip())
        self.assertEqual("255 (76)", self.ic._win.maxPixel.text().strip())
        self.assertEqual("0 (23)", self.ic._win.minPixel.text().strip())

        # Reset zoom
        self.ic._win.imageWidget.reset_zoom()

        # Update the GUI
        self.ic.updateStatus()

        # Check the information on the gui
        self.assertEqual("10", self.ic._win.lblXsize.text().strip())
        self.assertEqual("10", self.ic._win.lblYsize.text().strip())
        self.assertEqual("0", self.ic._win.deadPixel.text().strip())
        self.assertEqual("255", self.ic._win.maxPixel.text().strip())
        self.assertEqual("0", self.ic._win.minPixel.text().strip())
