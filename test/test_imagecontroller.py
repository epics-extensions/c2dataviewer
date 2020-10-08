# -*- coding: utf-8 -*-

"""
Copyright 2020 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Unit tests for Imagev

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""

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


from xvfbwrapper import Xvfb

class TestImageDisplay(unittest.TestCase):

    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.

        :return:
        """
        # Create virtual desktop so it can be run on headless platform
        self.xvfb = Xvfb(width=1280, height=720)
        self.xvfb.start()

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
        self.xvfb.stop()

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
