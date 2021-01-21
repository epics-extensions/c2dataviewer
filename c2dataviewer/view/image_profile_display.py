# -*- coding: utf-8 -*-

"""
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

        # Mutex to protect the data variable as set_image_data and plot are
        # called from the different threads
        self._data_mutex = pg.Qt.QtCore.QMutex()

        # Status of the profiles UI
        self._display_profiles = False

        # Save the reference to the image widget
        self._image_widget = self._grid.itemAtPosition(1, 1)

        # Build the X profile graph widget
        self._plot_x_profile = self._grid.itemAtPosition(0, 1)
        self._plot_x_profile.widget().getPlotItem().hideAxis('bottom')
        self._plot_x_profile.widget().getPlotItem().hideAxis('left')

        plot_x_size_policy = pg.Qt.QtGui.QSizePolicy(pg.Qt.QtGui.QSizePolicy.Fixed, pg.Qt.QtGui.QSizePolicy.Fixed)
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

        plot_y_size_policy = pg.Qt.QtGui.QSizePolicy(pg.Qt.QtGui.QSizePolicy.Fixed, pg.Qt.QtGui.QSizePolicy.Fixed)
        plot_y_size_policy.setHeightForWidth(self._plot_y_profile.widget().sizePolicy().hasHeightForWidth())
        self._plot_y_profile.widget().setSizePolicy(plot_y_size_policy)

        self._profile_y_curves = {
            'mono'  : self._plot_y_profile.widget().plot(pen=pg.mkPen(color=(255,255,255), style=pg.Qt.QtCore.Qt.SolidLine)),
            'red'   : self._plot_y_profile.widget().plot(pen=pg.mkPen(color=(255,  0,  0), style=pg.Qt.QtCore.Qt.SolidLine)),
            'green' : self._plot_y_profile.widget().plot(pen=pg.mkPen(color=(  0,255,  0), style=pg.Qt.QtCore.Qt.DashLine)),
            'blue'  : self._plot_y_profile.widget().plot(pen=pg.mkPen(color=(  0,255,255), style=pg.Qt.QtCore.Qt.DashDotLine)),
        }
        for curve in self._profile_y_curves.values():
            curve.rotate(-90)

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
        self._data = np.copy(data)
        self._data_color_mode = color_mode
        self._data_mutex.unlock()


    def plot(self, display_width, display_height):
        """
        Plot the profiles. This method does nothing if profiles are disabled.

        :param display_width: (int) Image width size on display in pixels.
        :param display_height: (int) Image height size on display in pixels.
        :return: None
        """
        # Return if profiles are not shown
        if not self._display_profiles:
            return

        # Calculate profiles
        x_profile, y_profile =  self._calculate_profiles()

        # Setup correct dimensions for the plots
        self._plot_x_profile.widget().setMinimumWidth(display_width)
        self._plot_x_profile.widget().setMaximumWidth(display_width)

        self._plot_y_profile.widget().setMinimumHeight(display_height)
        self._plot_y_profile.widget().setMaximumHeight(display_height)

        self._grid.update()

        # Draw X profile curves
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

    def show(self, flag):
        """
        Hide or show the profiles. This method should be called from the UI thread.

        :param flag: (bool) True to show the profiles, False otherwise.
        :return:
        """
        if flag:
            self._grid.removeItem(self._image_widget)
            self._grid.addItem(self._image_widget, 1, 1)
            self._grid.addItem(self._plot_x_profile, 0, 1, 1, 1, pg.Qt.QtCore.Qt.AlignLeft | pg.Qt.QtCore.Qt.AlignBottom)
            self._grid.addItem(self._plot_y_profile, 1, 0, 1, 1, pg.Qt.QtCore.Qt.AlignRight | pg.Qt.QtCore.Qt.AlignTop)
            self._plot_x_profile.widget().show()
            self._plot_y_profile.widget().show()
            self._display_profiles = True

        else:
            self._grid.removeItem(self._image_widget)
            self._grid.removeItem(self._plot_x_profile)
            self._grid.removeItem(self._plot_y_profile)
            self._grid.addItem(self._image_widget, 1, 1)
            self._plot_x_profile.widget().hide()
            self._plot_y_profile.widget().hide()
            self._display_profiles = False

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
        self._data_mutex.lock()
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
        self._data_mutex.unlock()

        return x_profile, y_profile
