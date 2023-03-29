# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2021 UChicago Argonne LLC
 as operator of Argonne National Laboratory

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""
import numpy as np

# Area detector color modes values. Source: https://github.com/areaDetector/ADCore/blob/master/ADApp/ADSrc/NDArray.h#L29
# Currently only four are supported.
COLOR_MODE_MONO = 0 # [NX, NY]
COLOR_MODE_RGB1 = 2 # [3, NX, NY]
COLOR_MODE_RGB2 = 3 # [NX, 3, NY]
COLOR_MODE_RGB3 = 4 # [NX, NY, 3]

COLOR_MODES = {
    COLOR_MODE_MONO : "MONO",
    COLOR_MODE_RGB1 : "RGB1",
    COLOR_MODE_RGB2 : "RGB2",
    COLOR_MODE_RGB3 : "RGB3",
}

def transcode_image(image, color_mode, x, y, z):
    """
    Transcode the numpy array to the correct shape.
    For MONO images this is [NX, NY] and for the RGB [NX, NY, 3] as documented:
    https://github.com/pyqtgraph/pyqtgraph/blob/ea08dda62dade523f2193ec353b9bacac6d8d35d/pyqtgraph/widgets/RawImageWidget.py#L41

    :param image: (numpy array) Flat image to be trancoded.
    :param color_mode: (enum) Color mode of the image.
    :param x: (int) X dimension of the image.
    :param y: (int) Y dimension of the image.
    :param z: (int) Z dimension of the image. Can be None for mono images.
    :return: (numpy array) Transcoded np.array in either [NX, NY] or [NX, NY, 3] shapes.
    """

    if color_mode == COLOR_MODE_MONO:
        return np.reshape(image, (y, x))

    elif color_mode == COLOR_MODE_RGB1:
        image = np.reshape(image, (y, x, z))
        return image

    elif color_mode == COLOR_MODE_RGB2:
        image = np.reshape(image, (y, z, x))
        image = np.swapaxes(image, 2, 1)
        return image

    elif color_mode == COLOR_MODE_RGB3:
        image = np.reshape(image, (z, y, x))
        image = np.swapaxes(image, 0, 2)
        image = np.swapaxes(image, 0, 1)
        return image

    else:
        raise RuntimeError("Unsupported color mode.")
