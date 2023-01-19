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
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtWidgets

from c2dataviewer.imagev import ImageWindow
from .helper import setup_qt_app

os.environ["QT_QPA_PLATFORM"] = "offscreen"

class TestImagev(unittest.TestCase):

    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.

        :return:
        """

        # Create Qt application
        setup_qt_app()
        
        # Build image window
        self.window = ImageWindow()
        self.window.resize(1200, 1200)
        QtWidgets.QApplication.instance().processEvents()

    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """

    def test_widgetVisibility2WindowSize(self):
        """
        Test if widgets start to disappear if window
        is resized to smallest possible size.

        As this gets really complex because of the relative coordinates,
        map everything to global (screen) coordinates and test in global space

        """

        # Get main window handle
        mainWindow = self.window

        # Get all child widgets
        widgets = mainWindow.findChildren(QtWidgets.QWidget)

        def pointOnMainWindow(point):

            # Get main window global coordinates
            mainWindowGeometry = mainWindow.geometry()
            mainWindowTopLeft = mainWindow.mapToGlobal(QtCore.QPoint(0, 0))
            mainWindowTopRight = mainWindow.mapToGlobal(QtCore.QPoint(mainWindowGeometry.width(), 0))
            mainWindowBottomLeft = mainWindow.mapToGlobal(QtCore.QPoint(0, mainWindowGeometry.height()))
            #mainWindowBottomRight = mainWindow.mapToGlobal(QPoint(mainWindowGeometry.width(), mainWindowGeometry.height()))

            if (point.x() >= mainWindowTopLeft.x() and
                point.x() <= mainWindowTopRight.x() and
                point.y() >= mainWindowTopLeft.y() and
                point.y() <= mainWindowBottomLeft.y()):
                return True
            else :
                return False

        def testWidgetsIfOnMainScreen():

            # Loop over them and see if they are all contained in a main window
            for _, w in enumerate(widgets):

                # Skip QSizeGrip (Handle which can be clicked with a mouse to resize the window)
                # as this is part of the window itself and is always out of the "canvas"
                if isinstance(w, QtWidgets.QSizeGrip):
                    continue

                self.assertTrue(pointOnMainWindow(w.mapToGlobal(QtCore.QPoint(0, 0))),
                        f"Testing top-left corner of {w.__class__.__name__} widget.")
                self.assertTrue(pointOnMainWindow(w.mapToGlobal(QtCore.QPoint(w.width(),0))),
                        f"Testing top-right corner of {w.__class__.__name__} widget.")
                self.assertTrue(pointOnMainWindow(w.mapToGlobal(QtCore.QPoint(0, w.height()))),
                        f"Testing bottom-left corner of {w.__class__.__name__} widget.")
                self.assertTrue(pointOnMainWindow(w.mapToGlobal(QtCore.QPoint(w.width(), w.height()))),
                        f"Testing bottom-right corner of {w.__class__.__name__} widget.")

        print(f"Testing widget visibility on default window size:")
        print(f"Window width: {mainWindow.geometry().width()}")
        print(f"Window height: {mainWindow.geometry().height()}")
        testWidgetsIfOnMainScreen()
