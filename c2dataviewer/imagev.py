
# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""

import sys
import os.path
import psutil
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt import uic
from pyqtgraph import QtCore
from .control import ImageController
from .model import DataSource as DataReceiver


form_path = os.path.join(os.path.dirname(__file__), "ui/imagev.ui")
form_class = uic.loadUiType(form_path)[0]

class ImageWindow(QtWidgets.QMainWindow, form_class):
    resized = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """

        :param parent:
        """
        super(ImageWindow, self).__init__(parent=parent)
        self._proc = psutil.Process()
        self.setupUi(self)
        self.show()

        self.resized.connect(self.resizedCallback)

    def resizeEvent(self, event):
        """

        :param event:
        :return:
        """
        self.resized.emit()
        return super(ImageWindow, self).resizeEvent(event)

    def resizedCallback(self):
        """

        :return:
        """
        self.imageWidget.set_scaling()


settings_dialog_path = os.path.join(os.path.dirname(__file__), "ui/imagev_settings.ui")
settings_dialog_class = uic.loadUiType(settings_dialog_path)[0]

class ImageSettingsDialog(QtWidgets.QDialog, settings_dialog_class):
    def __init__(self, parent=None):
        super(ImageSettingsDialog, self).__init__(parent=parent)
        self.setupUi(self)


warning_path = os.path.join(os.path.dirname(__file__), "ui/warning.ui")
warning_class = uic.loadUiType(warning_path)[0]

class WarningDialog(QtWidgets.QDialog, warning_class):
    def __init__(self, parent=None):
        super(WarningDialog, self).__init__(parent=parent)
        self.setupUi(self)

def imagev(pv, scale=None, noAGC=True):
    """
    Main function for image display

    :param pv: dictionary, which host all pv names
    :param label: label to identify PVs
    :param scale: scaling factor relative to 800xYYYY, 1.0 by default
    :param noAGC: No automatic gain adjust, True by default
    :return:
    """

    # Check for an instance of a QtWidgets.QApplication, if so use it...
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    else:
        print('QApplication instance already exists: %s' % str(app))

    if pv is None:
        label = None
    else:
        label = list(pv.keys())
        
    w = ImageWindow(None)
    data = DataReceiver(QtCore.QTimer, default=None)
    w.imageWidget.set_datasource(data)

    settings_dialog = ImageSettingsDialog(None)
    warning = WarningDialog(None)
    ImageController(w, IMAGE_SETTINGS_DIALOG = settings_dialog, WARNING=warning,
                    PV=label, timer=QtCore.QTimer(), data=data)

    # set initial scaling factor
    if scale is not None and scale != 1.0:
        w.imageWidget.set_scaling(scale=scale)
    else:
        w.imageWidget.set_scaling()

    if not noAGC:
        w.imageWidget.enable_auto_gain()

    if (label == None):
        msg = "No input channel specified, please add it manually in the Camera textbox."
        warning.warningTextBrowse.setText(msg)
        warning.show()
        warning.warningConfirmButton.clicked.connect(warning.close)

    w.show()
    sys.exit(app.exec_())
