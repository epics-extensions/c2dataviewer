# -*- coding: utf-8 -*-

"""
Copyright 2020 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Unit tests for Imagev

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""

import sys
import unittest
from PyQt5.QtWidgets import QWidget

from pyqtgraph.Qt import QtWidgets
from c2dataviewer.imagev import ImageWindow


app = QtWidgets.QApplication(sys.argv)

class TestImagev(unittest.TestCase):

    def setUp(self):
        self.window = ImageWindow()

    def test_widgetVisibility2WindowSize(self):
        """
        Test if widgets start to disappear if window
        is resized to smallest possible size.
        """

        # Get main window handle
        mainWindow = self.window

        def testChildVisibility():
            # Get parent geometry
            mainWindowGeometry = mainWindow.geometry()

            # Get all child widgets
            widgets = mainWindow.findChildren(QWidget)

            # Loop over them and see if they are all contained in a main window
            for _, w in enumerate(widgets):
                self.assertTrue(mainWindowGeometry.contains(w.geometry()), f"Size check failed at: w:{mainWindow.width()} h:{mainWindow.height()}")

        # Iterate over width dimension
        while mainWindow.width() > mainWindow.minimumWidth():
            testChildVisibility()
            mainWindow.resize(mainWindow.width() - 1, mainWindow.height())

        # Iterate over height dimension
        while mainWindow.height() > mainWindow.minimumHeight():
            testChildVisibility()
            mainWindow.resize(mainWindow.width(), mainWindow.height() - 1)

        # Check the smallest possible size again
        mainWindow.resize(0, 0)
        testChildVisibility()
