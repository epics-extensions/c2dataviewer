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
import pyqtgraph as pg
from .image_definitions import COLOR_MODE_MONO


class ImageProfileWidget(object):
    """
    Part of PVA object viewer utilities, it is responsible to
    display and image profiles.
    """

#########################################
#   Public interface
#########################################

    def __init__(self, canvas_grid_reference):
        super().__init__()

        # Reference to the canvas grid where the image and profiles are displayed.
        self._grid = canvas_grid_reference

        # Internal Numpy array holding image data
        self._data = None
        self._data_color_mode = None

        # Profiles of the data
        self._x_profile = None
        self._y_profile = None

        # Mutex to protect the data variable as set_image_data and plot are
        # called from the different threads
        self._data_mutex = pg.Qt.QtCore.QMutex()

        # Status of the profiles UI
        self._display_widget = False
        self._display_profiles = False
        self._display_rulers = False

        # Image dimensions
        self._nx = 0
        self._ny = 0

        # Save the reference to the image widget
        self._image_widget = self._grid.itemAtPosition(1, 1)

        # Build the X profile graph widget
        self._plot_x_profile = self._grid.itemAtPosition(0, 1)
        self._plot_x_profile.widget().getPlotItem().hideAxis('bottom')
        self._plot_x_profile.widget().getPlotItem().hideAxis('left')
        self._max_x_profile_height = self._plot_x_profile.widget().maximumHeight()
        self._x_axis_min = 0
        self._x_axis_max = 0

        plot_x_size_policy = pg.Qt.QtWidgets.QSizePolicy(pg.Qt.QtWidgets.QSizePolicy.Fixed, pg.Qt.QtWidgets.QSizePolicy.Fixed)
        plot_x_size_policy.setHeightForWidth(self._plot_x_profile.widget().sizePolicy().hasHeightForWidth())
        self._plot_x_profile.widget().setSizePolicy(plot_x_size_policy)

        self._profile_x_curves = {
            'mono'  : self._plot_x_profile.widget().plot(pen=pg.mkPen(color=(255,255,255), style=pg.Qt.QtCore.Qt.SolidLine)),
            'red'   : self._plot_x_profile.widget().plot(pen=pg.mkPen(color=(255,  0,  0), style=pg.Qt.QtCore.Qt.SolidLine)),
            'green' : self._plot_x_profile.widget().plot(pen=pg.mkPen(color=(  0,255,  0), style=pg.Qt.QtCore.Qt.DashLine)),
            'blue'  : self._plot_x_profile.widget().plot(pen=pg.mkPen(color=(  0,255,255), style=pg.Qt.QtCore.Qt.DashDotLine)),
        }

        # Build the Y profile graph widget
        self._plot_y_profile = self._grid.itemAtPosition(1, 0)
        self._plot_y_profile.widget().getPlotItem().hideAxis('bottom')
        self._plot_y_profile.widget().getPlotItem().hideAxis('left')
        self._max_y_profile_width = self._plot_y_profile.widget().maximumWidth()
        self._y_axis_min = 0
        self._y_axis_max = 0

        plot_y_size_policy = pg.Qt.QtWidgets.QSizePolicy(pg.Qt.QtWidgets.QSizePolicy.Fixed, pg.Qt.QtWidgets.QSizePolicy.Fixed)
        plot_y_size_policy.setHeightForWidth(self._plot_y_profile.widget().sizePolicy().hasHeightForWidth())
        self._plot_y_profile.widget().setSizePolicy(plot_y_size_policy)

        self._profile_y_curves = {
            'mono'  : self._plot_y_profile.widget().plot(pen=pg.mkPen(color=(255,255,255), style=pg.Qt.QtCore.Qt.SolidLine)),
            'red'   : self._plot_y_profile.widget().plot(pen=pg.mkPen(color=(255,  0,  0), style=pg.Qt.QtCore.Qt.SolidLine)),
            'green' : self._plot_y_profile.widget().plot(pen=pg.mkPen(color=(  0,255,  0), style=pg.Qt.QtCore.Qt.DashLine)),
            'blue'  : self._plot_y_profile.widget().plot(pen=pg.mkPen(color=(  0,255,255), style=pg.Qt.QtCore.Qt.DashDotLine)),
        }

        transform = pg.QtGui.QTransform()
        transform.rotate(-90)
        for curve in self._profile_y_curves.values():
            curve.setTransform(transform)

        # Hide profiles by default
        self._plot_x_profile.widget().hide()
        self._plot_y_profile.widget().hide()
        self._grid.removeItem(self._plot_x_profile)
        self._grid.removeItem(self._plot_y_profile)
        self._grid.removeItem(self._image_widget)
        self._grid.addItem(self._image_widget, 0, 0)

    def set_image_data(self, data, color_mode):
        """
        Make an internal copy of the data image.

        :param data: (Numpy arrray) Image of the data as the Numpy array.
        :param color_mode: (enum) Code of the color mode.
        :return: None
        """
        self._data_mutex.lock()
        try:
            shape = data.shape
            if len(shape):
                self._nx = shape[0]
                self._ny = shape[1]
            self._data_color_mode = color_mode
            if not self._display_profiles:
                return
            self._data = np.copy(data)
            self._x_profile, self._y_profile = self._calculate_profiles()
        finally:
            self._data_mutex.unlock()

    def plot(self, display_width, display_height):
        """
        Plot the profiles. This method does nothing if profiles are disabled.

        :param display_width: (int) Image width size on display in pixels.
        :param display_height: (int) Image height size on display in pixels.
        :return: None
        """
        # Return if profiles are not shown
        if not self._display_widget:
            return

        # Setup correct dimensions for the plots
        self._plot_x_profile.widget().setMinimumWidth(int(display_width))
        self._plot_x_profile.widget().setMaximumWidth(int(display_width))
        self._plot_x_profile.widget().setMaximumHeight(self._max_x_profile_height)

        self._plot_y_profile.widget().setMinimumHeight(int(display_height))
        self._plot_y_profile.widget().setMaximumHeight(int(display_height))
        self._plot_x_profile.widget().setMaximumWidth(self._max_y_profile_width)

        if self._x_axis_max:
            self._plot_x_profile.widget().getPlotItem().getAxis('bottom').setRange(self._x_axis_min,self._x_axis_max)
        else:
            self._plot_x_profile.widget().getPlotItem().getAxis('bottom').setRange(0, self._nx)
        if self._y_axis_max:
            self._plot_y_profile.widget().getPlotItem().getAxis('right').setRange(self._y_axis_max,self._y_axis_min)
        else:
            self._plot_y_profile.widget().getPlotItem().getAxis('right').setRange(self._ny, 0)

        if not self._display_profiles:
            self._plot_x_profile.widget().setMaximumHeight(0)
            self._plot_y_profile.widget().setMaximumWidth(0)

        self._grid.update()

        if not self._display_profiles:
            return

        # Calculate profiles
        x_profile, y_profile =  self._x_profile, self._y_profile

        # Draw X profile curves
        self._data_mutex.lock()
        if type(x_profile) is list:
            for mode, curve in self._profile_x_curves.items():
                if mode == 'red':
                    curve.setData(x_profile[0])
                    curve.show()
                elif mode == 'green':
                    curve.setData(x_profile[1])
                    curve.show()
                elif mode == 'blue':
                    curve.setData(x_profile[2])
                    curve.show()
                else:
                    curve.hide()
        else:
            for mode, curve in self._profile_x_curves.items():
                if mode == 'mono':
                    curve.setData(x_profile)
                    curve.show()
                else:
                    curve.hide()

        # Draw Y profile curves
        if type(y_profile) is list:
            for mode, curve in self._profile_y_curves.items():
                if mode == 'red':
                    curve.setData(y_profile[0])
                    curve.show()
                elif mode == 'green':
                    curve.setData(y_profile[1])
                    curve.show()
                elif mode == 'blue':
                    curve.setData(y_profile[2])
                    curve.show()
                else:
                    curve.hide()
        else:
            for mode, curve in self._profile_y_curves.items():
                if mode == 'mono':
                    curve.setData(y_profile)
                    curve.show()
                else:
                    curve.hide()
        self._data_mutex.unlock()

    def setXAxisRange(self, xmin=0, xmax=0):
        """
        Set range for x axis.

        :param xmin: (float) x axis min value
        :param xmax: (float) x axis max value
        :return:
        """
        self._x_axis_min = xmin
        self._x_axis_max = xmax

    def setYAxisRange(self, ymin=0, ymax=0):
        """
        Set range for y axis.

        :param ymin: (float) y axis min value
        :param ymax: (float) y axis max value
        :return:
        """
        self._y_axis_min = ymin
        self._y_axis_max = ymax

    def showProfiles(self, displayProfiles=None):
        """
        Display profiles. This method should be called from the UI thread.

        :param displayProfiles: (bool) True to show the profiles, False otherwise.
        :return:
        """
        if displayProfiles is not None:
            self._display_profiles = displayProfiles

        if not self._display_profiles:
            for curve in self._profile_x_curves.values():
                curve.hide()
            for curve in self._profile_y_curves.values():
                curve.hide()

    def showRulers(self, displayRulers=None):
        """
        Display rulers. This method should be called from the UI thread.

        :param displayRulers: (bool) True to show the rulers, False otherwise.
        :return:
        """
        if displayRulers is not None:
            self._display_rulers = displayRulers
        if self._display_rulers:
            self._plot_x_profile.widget().getPlotItem().showAxis('bottom')
            self._plot_y_profile.widget().getPlotItem().showAxis('right')
        else:
            self._plot_x_profile.widget().getPlotItem().hideAxis('bottom')
            self._plot_y_profile.widget().getPlotItem().hideAxis('right')

    def show(self, displayWidget):
        """
        Hide or show the widget. This method should be called from the UI thread.

        :param displayWidget: (bool) True to show the widget, False otherwise.
        :return:
        """
        if displayWidget:
            self._grid.removeItem(self._image_widget)
            self._grid.addItem(self._image_widget, 1, 1)
            self._grid.addItem(self._plot_x_profile, 0, 1, 1, 1, pg.Qt.QtCore.Qt.AlignLeft | pg.Qt.QtCore.Qt.AlignBottom)
            self._grid.addItem(self._plot_y_profile, 1, 0, 1, 1, pg.Qt.QtCore.Qt.AlignRight | pg.Qt.QtCore.Qt.AlignTop)
            self._plot_x_profile.widget().show()
            self._plot_y_profile.widget().show()
            self._display_widget = True
        else:
            self._grid.removeItem(self._image_widget)
            self._grid.removeItem(self._plot_x_profile)
            self._grid.removeItem(self._plot_y_profile)
            self._grid.addItem(self._image_widget, 1, 1)
            self._plot_x_profile.widget().hide()
            self._plot_y_profile.widget().hide()
            self._display_widget = False

        self._grid.update()

#########################################
#   Internal methods
#########################################

    def _calculate_profiles(self):
        """
        Calculate the profiles.

        :return: (numpy array, numpy array) X and Y profiles of the image.
        """
        # Calculate the profiles
        x_profile = y_profile = None
        if self._data_color_mode == COLOR_MODE_MONO:
            x_profile = self._data.mean(axis=1)
            y_profile = self._data.mean(axis=0)
        else:
            x_profile = []
            y_profile = []
            for i in range(3):
                x_profile.append(self._data[:,:,i].mean(axis=1))
                y_profile.append(self._data[:,:,i].mean(axis=0))

        return x_profile, y_profile
