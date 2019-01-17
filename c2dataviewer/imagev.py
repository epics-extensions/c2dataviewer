
# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""

import sys
import psutil
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt import uic
from pyqtgraph import QtCore
from .control import ImageController
from .modal import ImageData as DataReceiver


def imagev(pv, label, scale=1.0, noAGC=True):
    """
    Main function for image display

    :param pv: dictionary, which host all pv names
    :param label: label to identify PVs
    :param scale: scaling factor relative to 800xYYYY, 1.0 by default
    :param noAGC: No automatic gain adjust, True by default
    :return:
    """
    form_class = uic.loadUiType("c2dataviewer/ui/imagev.ui")[0]

    class ImageWindow(QtWidgets.QMainWindow, form_class):
        resized = QtCore.pyqtSignal()

        def __init__(self, parent=None):
            super(ImageWindow, self).__init__(parent=parent)
            self._proc = psutil.Process()
            self.setupUi(self)
            self.show()
            self.imageReceiver = None

            self.resized.connect(self.resizedCallback)

        def set_imagereceiver(self, imageReceiver):
            """

            :return:
            """
            self.imageReceiver = imageReceiver

        def doResize(self):
            try:
                # print("I am in doResize")
                # sbh = self._statusbar.height()
                x = self.imageReceiver.x
                y = self.imageReceiver.y
                self._scale = 840.0/x
                self.resize(x * self._scale, y * self._scale)
                self.imageWidget.set_scaling(self._scale, x, y)
            except:
                pass

        def resizeEvent(self, event):
            self.resized.emit()
            return super(ImageWindow, self).resizeEvent(event)

        def resizedCallback(self):
            x = self.imageReceiver.x
            # print("I am in resizeCallback")
            try:
                self._scale = self.width() / x
                self.imageWidget.set_scaling(self._scale)
            except:
                self._scale = 1.0

    dlg_class = uic.loadUiType("c2dataviewer/ui/imagev_limit_pane.ui")[0]

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

    data = DataReceiver(QtCore.QTimer(), default=pv)
    w = ImageWindow(None)
    dlg = LimitDiaglog(None)
    data.config(w)
    ImageController(w, LIMIT=dlg, PV=label, timer=QtCore.QTimer(), data=data)
    w.set_imagereceiver(data)
    w.imageWidget.set_scaling(scale)
    if not noAGC:
        w.imageWidget.enable_auto_gain()

    w.show()
    sys.exit(app.exec_())
