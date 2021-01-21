# -*- coding: utf-8 -*-

"""
Copyright 2021 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Unit tests for image_definitions.py

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""
import os
import unittest
import numpy as np

from c2dataviewer.view.image_definitions import *
from .helper import create_image

os.environ["QT_QPA_PLATFORM"] = "offscreen"

class TestImageDefinitions(unittest.TestCase):

    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.

        :return:
        """
        pass


    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """
        pass

    def test_transcode_image(self):

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


        # Mono image
        data = create_image(1, arrayValue, data_type='ubyteValue', nx=x, ny=y, color_mode=COLOR_MODE_MONO)
        img = transcode_image(data['value'][0]['ubyteValue'], COLOR_MODE_MONO, 10, 10, None)
        np.testing.assert_equal(np.array([[255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],
                                        [255,   0,  77,  54,  23,  76,  34,  65,  34,  65],], dtype=np.uint8),
                                img
                                )

        # RGB1 image
        data = create_image(2, arrayValue*3, data_type='ubyteValue', nx=x, ny=y, nz=3, color_mode=COLOR_MODE_RGB1)
        img = transcode_image(data['value'][0]['ubyteValue'], COLOR_MODE_RGB1, 10, 10, 3)
        np.testing.assert_equal( np.array([[[255,   0,  77],
                                            [ 54,  23,  76],
                                            [ 34,  65,  34],
                                            [ 65, 255,   0],
                                            [ 77,  54,  23],
                                            [ 76,  34,  65],
                                            [ 34,  65, 255],
                                            [  0,  77,  54],
                                            [ 23,  76,  34],
                                            [ 65,  34,  65],] for i in range(x)], dtype=np.uint8),
                                img
                                )

        # RGB2 image
        data = create_image(3, arrayValue*3, data_type='ubyteValue', nx=x, ny=y, nz=3, color_mode=COLOR_MODE_RGB2)
        img = transcode_image(data['value'][0]['ubyteValue'], COLOR_MODE_RGB2, 10, 10, 3)
        np.testing.assert_equal( np.array([[[255, 255, 255,],
                                            [  0,   0,   0,],
                                            [ 77,  77,  77,],
                                            [ 54,  54,  54,],
                                            [ 23,  23,  23,],
                                            [ 76,  76,  76,],
                                            [ 34,  34,  34,],
                                            [ 65,  65,  65,],
                                            [ 34,  34,  34,],
                                            [ 65,  65,  65,],] for i in range(x)], dtype=np.uint8),
                                img
                                )



        # RGB3 image
        data = create_image(4, arrayValue*3, data_type='ubyteValue', nx=x, ny=y, nz=3, color_mode=COLOR_MODE_RGB3)
        img = transcode_image(data['value'][0]['ubyteValue'], COLOR_MODE_RGB3, 10, 10, 3)
        np.testing.assert_equal( np.array([[[255, 255, 255,],
                                            [  0,   0,   0,],
                                            [ 77,  77,  77,],
                                            [ 54,  54,  54,],
                                            [ 23,  23,  23,],
                                            [ 76,  76,  76,],
                                            [ 34,  34,  34,],
                                            [ 65,  65,  65,],
                                            [ 34,  34,  34,],
                                            [ 65,  65,  65,],] for i in range(x)], dtype=np.uint8),
                                img
                                )
