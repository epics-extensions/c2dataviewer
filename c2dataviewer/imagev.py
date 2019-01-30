
# -*- coding: utf-8 -*-

"""
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
from .model import ImageData as DataReceiver


def imagev(pv, label, scale=None, noAGC=True):
    """
    Main function for image display

    :param pv: dictionary, which host all pv names
    :param label: label to identify PVs
    :param scale: scaling factor relative to 800xYYYY, 1.0 by default
    :param noAGC: No automatic gain adjust, True by default
    :return:
    """
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

    dlg_path = os.path.join(os.path.dirname(__file__), "ui/imagev_limit_pane.ui")
    dlg_class = uic.loadUiType(dlg_path)[0]

    class LimitDiaglog(QtWidgets.QDialog, dlg_class):

        def __init__(self, parent=None):
            super(LimitDiaglog, self).__init__(parent=parent)
            self.setupUi(self)

    # Check for an instance of a QtWidgets.QApplication, if so use it...
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    else:
        print('QApplication instance already exists: %s' % str(app))

    w = ImageWindow(None)
    w.imageWidget.gain_controller(w.imageBlackSlider, w.imageGainSlider)
    data = DataReceiver(default=pv)
    w.imageWidget.set_datasource(data)

    dlg = LimitDiaglog(None)
    ImageController(w, LIMIT=dlg, PV=label, timer=QtCore.QTimer(), data=data)

    # set initial scaling factor
    if scale is not None and scale != 1.0:
        w.imageWidget.set_scaling(scale=scale)
    else:
        w.imageWidget.set_scaling()

    if not noAGC:
        w.imageWidget.enable_auto_gain()

    w.show()
    sys.exit(app.exec_())
