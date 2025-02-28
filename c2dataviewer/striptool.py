"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

import sys
import os
import psutil
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt import uic
from pyqtgraph.parametertree import Parameter
from .model import DataSource as DataReceiver
from .control import StripToolController
from .view import StripToolConfigure

form_path = os.path.join(os.path.dirname(__file__), "ui/striptool.ui")
form_class = uic.loadUiType(form_path)[0]

class StripToolWindow(QtWidgets.QMainWindow, form_class):
    def __init__(self, parent=None):
        super(StripToolWindow, self).__init__(parent=parent)
        self._proc = psutil.Process()
        self.setupUi(self)
        self.show()

pvedit_dialog_path = os.path.join(os.path.dirname(__file__), "ui/addpv.ui")
pvedit_dialog_class = uic.loadUiType(pvedit_dialog_path)[0]

class PvEditDialog(QtWidgets.QDialog, pvedit_dialog_class):
    def __init__(self, parent=None):
        super(PvEditDialog, self).__init__(parent=parent)
        self.setupUi(self)

warning_path = os.path.join(os.path.dirname(__file__), "ui/warning.ui")
warning_class = uic.loadUiType(warning_path)[0]

class WarningDialog(QtWidgets.QDialog, warning_class):
    def __init__(self, parent=None):
        super(WarningDialog, self).__init__(parent=parent)
        self.setupUi(self)

def striptool(cfg, **kwargs):
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    else:
        print('QApplication instance already exists: %s' % str(app))

    w = StripToolWindow()
    model = DataReceiver()
    warning = WarningDialog()
    pvedit_dialog = PvEditDialog()

    configure = StripToolConfigure(cfg, **kwargs)
    parameters = Parameter.create(
        name="params", type="group", children=configure.parse())
    w.parameterPane.setParameters(parameters, showTop=False)

    controller = StripToolController(w, model, pvedit_dialog, warning, parameters, cfg, **kwargs)
    parameters.sigTreeStateChanged.connect(controller.parameter_change)
    
    w.show()
    try:
        app.exec_()
    finally:
        controller.stop_plotting()
