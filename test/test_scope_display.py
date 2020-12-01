# -*- coding: utf-8 -*-

"""
Copyright 2020 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Unit tests for Scope application (scope_display.py)

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""
import os
import sys
import unittest
import numpy as np

from c2dataviewer.view.scope_display import PlotWidget
os.environ["QT_QPA_PLATFORM"] = "offscreen"

array1 = [
0.0, 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9,
10.0, 11.1, 12.2, 13.3, 14.4, 15.5, 16.6, 17.7, 18.8, 19.9,
20.0, 21.1, 22.2, 23.3, 24.4, 25.5, 26.6, 27.7, 28.8, 29.9,
30.0, 31.1, 32.2, 33.3, 34.4, 35.5, 36.6, 37.7, 38.8, 39.9,
40.0, 41.1, 42.2, 43.3, 44.4, 45.5, 46.6, 47.7, 48.8, 49.9,
]

class TestScopeDisplay(unittest.TestCase):

    def setUp(self):
        """
        Build the environment for each unit test case.
        This method is called before each test.

        :return:
        """
        # Create instance of the PlotWidget
        self.pw = PlotWidget()

    def tearDown(self):
        """
        Tear down the environment after each test case.
        This mentod is called after each test.

        :return:
        """
        pass


    def test_no_filter(self):
        """
        Calculate fft without any filter

        :return:
        """

        # Prepare data
        data = np.array(array1, dtype=np.float64)
        sample_period = np.diff(data).mean()

        # Calculate fft
        xf, yf = self.pw.calculate_ftt(data, sample_period, "fft", None)

        # Test result
        np.testing.assert_array_almost_equal(xf,
                                             np.array([0.,         0.01963928, 0.03927856, 0.05891784, 0.07855711, 0.09819639,
                                                       0.11783567, 0.13747495, 0.15711423, 0.17675351, 0.19639279, 0.21603206,
                                                       0.23567134, 0.25531062, 0.2749499 , 0.29458918, 0.31422846, 0.33386774,
                                                       0.35350701, 0.37314629, 0.39278557, 0.41242485, 0.43206413, 0.45170341,
                                                       0.47134269, 0.49098196,], dtype=np.float64),
                                            decimal=6)

        np.testing.assert_array_almost_equal(yf,
                                            np.array([24.95 , 15.926,  7.979,  5.337,  4.021,  3.56 ,  2.716,  2.349,
                                                       2.076,  1.866,  1.871,  1.569,  1.461,  1.372,  1.298,  1.36 ,
                                                       1.184,  1.141,  1.105,  1.076,  1.157,  1.032,  1.018,  1.008,
                                                       1.002,  1.1  ],
                                                    dtype=np.float64),
                                            decimal=3
                                        )

    def test_hamming_filter(self):
        """
        Calculate fft with Hamming filter

        :return:
        """

        # Prepare data
        data = np.array(array1, dtype=np.float64)
        sample_period = np.diff(data).mean()

        # Run transformation
        xf, yf = self.pw.calculate_ftt(data, sample_period, "psd", "hamming")

        # Check results
        np.testing.assert_array_almost_equal(xf,
                                             np.array([0.,         0.01963928, 0.03927856, 0.05891784, 0.07855711, 0.09819639,
                                                       0.11783567, 0.13747495, 0.15711423, 0.17675351, 0.19639279, 0.21603206,
                                                       0.23567134, 0.25531062, 0.2749499 , 0.29458918, 0.31422846, 0.33386774,
                                                       0.35350701, 0.37314629, 0.39278557, 0.41242485, 0.43206413, 0.45170341,
                                                       0.47134269, 0.49098196,], dtype=np.float64),
                                            decimal=6)
        np.testing.assert_array_almost_equal(yf,
                                            np.array([7.80679385e+05, 7.88967744e+05, 2.35308112e+03, 6.03251068e+01,
                                                      6.61654009e+01, 6.03079690e+02, 5.17923210e+01, 1.25620540e+02,
                                                      1.04688807e+02, 4.53016738e+01, 2.15743462e+02, 2.96731584e+01,
                                                      5.81910126e+01, 5.19148396e+01, 2.40652017e+01, 1.18719727e+02,
                                                      1.89395969e+01, 3.70000838e+01, 3.48239178e+01, 1.67868855e+01,
                                                      8.69944055e+01, 1.50511865e+01, 2.98263438e+01, 2.92627440e+01,
                                                      1.44786076e+01, 7.89336302e+01,],
                                                      dtype=np.float64),
                                            decimal=3
                                        )

    def test_exp_moving_average(self):
        """
        Calculate Exponential moving average.

        :return:
        """

        # Prepare data
        data = [ np.array(array1, dtype=np.float64) * d for d in range(1, 7) ]
        average = None

        self.pw.set_average(4)

        # Calculate moving averages
        average = self.pw.exponential_moving_average(data[0], average)
        np.testing.assert_array_almost_equal(average,
                                            np.array(
                                                [6.000e-11, 4.400e-01, 8.800e-01, 1.320e+00, 1.760e+00, 2.200e+00,
                                                2.640e+00, 3.080e+00, 3.520e+00, 3.960e+00, 4.000e+00, 4.440e+00,
                                                4.880e+00, 5.320e+00, 5.760e+00, 6.200e+00, 6.640e+00, 7.080e+00,
                                                7.520e+00, 7.960e+00, 8.000e+00, 8.440e+00, 8.880e+00, 9.320e+00,
                                                9.760e+00, 1.020e+01, 1.064e+01, 1.108e+01, 1.152e+01, 1.196e+01,
                                                1.200e+01, 1.244e+01, 1.288e+01, 1.332e+01, 1.376e+01, 1.420e+01,
                                                1.464e+01, 1.508e+01, 1.552e+01, 1.596e+01, 1.600e+01, 1.644e+01,
                                                1.688e+01, 1.732e+01, 1.776e+01, 1.820e+01, 1.864e+01, 1.908e+01,
                                                1.952e+01, 1.996e+01],
                                              dtype=np.float64),
                                              decimal=3)

        average = self.pw.exponential_moving_average(data[1], average)
        np.testing.assert_array_almost_equal(average,
                                            np.array(
                                                [3.6000e-11, 1.1440e+00, 2.2880e+00, 3.4320e+00, 4.5760e+00,
                                                5.7200e+00, 6.8640e+00, 8.0080e+00, 9.1520e+00, 1.0296e+01,
                                                1.0400e+01, 1.1544e+01, 1.2688e+01, 1.3832e+01, 1.4976e+01,
                                                1.6120e+01, 1.7264e+01, 1.8408e+01, 1.9552e+01, 2.0696e+01,
                                                2.0800e+01, 2.1944e+01, 2.3088e+01, 2.4232e+01, 2.5376e+01,
                                                2.6520e+01, 2.7664e+01, 2.8808e+01, 2.9952e+01, 3.1096e+01,
                                                3.1200e+01, 3.2344e+01, 3.3488e+01, 3.4632e+01, 3.5776e+01,
                                                3.6920e+01, 3.8064e+01, 3.9208e+01, 4.0352e+01, 4.1496e+01,
                                                4.1600e+01, 4.2744e+01, 4.3888e+01, 4.5032e+01, 4.6176e+01,
                                                4.7320e+01, 4.8464e+01, 4.9608e+01, 5.0752e+01, 5.1896e+01],
                                              dtype=np.float64),
                                              decimal=3)

        average = self.pw.exponential_moving_average(data[2], average)
        np.testing.assert_array_almost_equal(average,
                                            np.array(
                                                [2.16000e-11, 2.00640e+00, 4.01280e+00, 6.01920e+00, 8.02560e+00,
                                                1.00320e+01, 1.20384e+01, 1.40448e+01, 1.60512e+01, 1.80576e+01,
                                                1.82400e+01, 2.02464e+01, 2.22528e+01, 2.42592e+01, 2.62656e+01,
                                                2.82720e+01, 3.02784e+01, 3.22848e+01, 3.42912e+01, 3.62976e+01,
                                                3.64800e+01, 3.84864e+01, 4.04928e+01, 4.24992e+01, 4.45056e+01,
                                                4.65120e+01, 4.85184e+01, 5.05248e+01, 5.25312e+01, 5.45376e+01,
                                                5.47200e+01, 5.67264e+01, 5.87328e+01, 6.07392e+01, 6.27456e+01,
                                                6.47520e+01, 6.67584e+01, 6.87648e+01, 7.07712e+01, 7.27776e+01,
                                                7.29600e+01, 7.49664e+01, 7.69728e+01, 7.89792e+01, 8.09856e+01,
                                                8.29920e+01, 8.49984e+01, 8.70048e+01, 8.90112e+01, 9.10176e+01],
                                              dtype=np.float64),
                                              decimal=3)

        average = self.pw.exponential_moving_average(data[3], average)
        np.testing.assert_array_almost_equal(average,
                                            np.array(
                                                [1.2960000e-11, 2.9638400e+00, 5.9276800e+00, 8.8915200e+00,
                                                1.1855360e+01, 1.4819200e+01, 1.7783040e+01, 2.0746880e+01,
                                                2.3710720e+01, 2.6674560e+01, 2.6944000e+01, 2.9907840e+01,
                                                3.2871680e+01, 3.5835520e+01, 3.8799360e+01, 4.1763200e+01,
                                                4.4727040e+01, 4.7690880e+01, 5.0654720e+01, 5.3618560e+01,
                                                5.3888000e+01, 5.6851840e+01, 5.9815680e+01, 6.2779520e+01,
                                                6.5743360e+01, 6.8707200e+01, 7.1671040e+01, 7.4634880e+01,
                                                7.7598720e+01, 8.0562560e+01, 8.0832000e+01, 8.3795840e+01,
                                                8.6759680e+01, 8.9723520e+01, 9.2687360e+01, 9.5651200e+01,
                                                9.8615040e+01, 1.0157888e+02, 1.0454272e+02, 1.0750656e+02,
                                                1.0777600e+02, 1.1073984e+02, 1.1370368e+02, 1.1666752e+02,
                                                1.1963136e+02, 1.2259520e+02, 1.2555904e+02, 1.2852288e+02,
                                                1.3148672e+02, 1.3445056e+02],
                                              dtype=np.float64),
                                              decimal=3)

        average = self.pw.exponential_moving_average(data[4], average)
        np.testing.assert_array_almost_equal(average,
                                            np.array(
                                                [7.77600000e-12, 3.97830400e+00, 7.95660800e+00, 1.19349120e+01,
                                                1.59132160e+01, 1.98915200e+01, 2.38698240e+01, 2.78481280e+01,
                                                3.18264320e+01, 3.58047360e+01, 3.61664000e+01, 4.01447040e+01,
                                                4.41230080e+01, 4.81013120e+01, 5.20796160e+01, 5.60579200e+01,
                                                6.00362240e+01, 6.40145280e+01, 6.79928320e+01, 7.19711360e+01,
                                                7.23328000e+01, 7.63111040e+01, 8.02894080e+01, 8.42677120e+01,
                                                8.82460160e+01, 9.22243200e+01, 9.62026240e+01, 1.00180928e+02,
                                                1.04159232e+02, 1.08137536e+02, 1.08499200e+02, 1.12477504e+02,
                                                1.16455808e+02, 1.20434112e+02, 1.24412416e+02, 1.28390720e+02,
                                                1.32369024e+02, 1.36347328e+02, 1.40325632e+02, 1.44303936e+02,
                                                1.44665600e+02, 1.48643904e+02, 1.52622208e+02, 1.56600512e+02,
                                                1.60578816e+02, 1.64557120e+02, 1.68535424e+02, 1.72513728e+02,
                                                1.76492032e+02, 1.80470336e+02],
                                              dtype=np.float64),
                                              decimal=3)

        average = self.pw.exponential_moving_average(data[5], average)
        np.testing.assert_array_almost_equal(average,
                                            np.array(
                                                [4.66560000e-12, 5.02698240e+00, 1.00539648e+01, 1.50809472e+01,
                                                2.01079296e+01, 2.51349120e+01, 3.01618944e+01, 3.51888768e+01,
                                                4.02158592e+01, 4.52428416e+01, 4.56998400e+01, 5.07268224e+01,
                                                5.57538048e+01, 6.07807872e+01, 6.58077696e+01, 7.08347520e+01,
                                                7.58617344e+01, 8.08887168e+01, 8.59156992e+01, 9.09426816e+01,
                                                9.13996800e+01, 9.64266624e+01, 1.01453645e+02, 1.06480627e+02,
                                                1.11507610e+02, 1.16534592e+02, 1.21561574e+02, 1.26588557e+02,
                                                1.31615539e+02, 1.36642522e+02, 1.37099520e+02, 1.42126502e+02,
                                                1.47153485e+02, 1.52180467e+02, 1.57207450e+02, 1.62234432e+02,
                                                1.67261414e+02, 1.72288397e+02, 1.77315379e+02, 1.82342362e+02,
                                                1.82799360e+02, 1.87826342e+02, 1.92853325e+02, 1.97880307e+02,
                                                2.02907290e+02, 2.07934272e+02, 2.12961254e+02, 2.17988237e+02,
                                                2.23015219e+02, 2.28042202e+02],
                                              dtype=np.float64),
                                              decimal=3)

    def test_multi_axis_plot(self):
        """
        Test multi axis plot.

        :return:
        """
        signals = ["x1", "x1", "x1", "x1"]

        self.pw.setup_plot(signals, single_axis=False)

        self.assertIsNotNone(self.pw.plot)
        self.assertEqual(len(signals), len(self.pw.axis))
        self.assertEqual(len(signals), len(self.pw.views))
        self.assertEqual(len(signals), len(self.pw.curves))
