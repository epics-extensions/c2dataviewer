# -*- coding: utf-8 -*-

"""
Copyright 2021 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Unit tests for ImageProfileWidget

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""
import sys
import os
import unittest
import unittest.mock as mock
import numpy as np
import pyqtgraph as pg

from c2dataviewer.imagev import ImageWindow, ImageSettingsDialog, WarningDialog
from c2dataviewer.control.imagecontroller import ImageController
from c2dataviewer.view.image_definitions import COLOR_MODE_MONO, COLOR_MODE_RGB2, transcode_image
from c2dataviewer.view.image_profile_display import ImageProfileWidget
from .helper import create_image
from .helper import setup_qt_app

os.environ["QT_QPA_PLATFORM"] = "offscreen"


class TestImageProfileWidget(unittest.TestCase):

    
    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.
        We need the whole application to be able to test this, as ImageProfileWidget also handle the layout.

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
                PV={'test', 'test'}, timer=pg.Qt.QtCore.QTimer(), data=None)

        
        # Get ImageProfileWidget
        self.w = self.ic._win.imageWidget.image_profile_widget


    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """

    def test_calculate_profiles(self):
        """
        Test if profile calculation is correct.

        :return:
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

        # Test with the mono image
        data = create_image(1, arrayValue, data_type='ubyteValue', nx=10, ny=10, color_mode=COLOR_MODE_MONO)
        data = transcode_image(data['value'][0]['ubyteValue'], COLOR_MODE_MONO, 10, 10, None)
        self.w.set_image_data(data, COLOR_MODE_MONO)
        x_profile, y_profile = self.w._calculate_profiles()

        np.testing.assert_equal(np.array([68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3],
                                        dtype=np.double),
                                x_profile
                        )
        np.testing.assert_equal(np.array([255.,   0.,  77.,  54.,  23.,  76.,  34.,  65.,  34.,  65.],
                                        dtype=np.double),
                                y_profile
                        )

        # Test with the color image
        data = create_image(3, arrayValue*3, data_type='ubyteValue', nx=10, ny=10, nz=3, color_mode=COLOR_MODE_RGB2)
        data = transcode_image(data['value'][0]['ubyteValue'], COLOR_MODE_RGB2, 10, 10, 3)
        self.w.set_image_data(data, COLOR_MODE_RGB2)
        x_profile, y_profile = self.w._calculate_profiles()

        np.testing.assert_equal(np.array([  [68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3],
                                            [68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3],
                                            [68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3, 68.3],],
                                        dtype=np.double),
                                x_profile
                        )
        np.testing.assert_equal(np.array([  [255.,   0.,  77.,  54.,  23.,  76.,  34.,  65.,  34.,  65.],
                                            [255.,   0.,  77.,  54.,  23.,  76.,  34.,  65.,  34.,  65.],
                                            [255.,   0.,  77.,  54.,  23.,  76.,  34.,  65.,  34.,  65.],],
                                        dtype=np.double),
                                y_profile
                        )
