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
from pyqtgraph.parametertree import Parameter
from .view import Configure
from .model import ScopeData
from .control import ScopeController


def scope(cfg, **kargs):
    """
    Main function for scope display

    :return:
    """
    form_path = os.path.join( os.path.dirname(__file__), "ui/scope.ui")
    form_class = uic.loadUiType(form_path)[0]

    class ScopeWindow(QtWidgets.QMainWindow, form_class):
        def __init__(self, parent=None):
            super(ScopeWindow, self).__init__(parent=parent)
            self._proc = psutil.Process()
            self.setupUi(self)
            self.show()

    # Check for an instance of a QtWidgets.QApplication, if so use it...
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    else:
        print('QApplication instance already exists: %s' % str(app))

    w = ScopeWindow()

    configure = Configure(cfg, **kargs)
    parameters = Parameter.create(name="params", type="group", children=configure.parse())
    w.parameterPane.setParameters(parameters, showTop=False)
    pvmap = configure.pvs

    if pvmap is not None:
        model = ScopeData(pv=list(pvmap.values())[0])
        controller = ScopeController(w, model, parameters)
        controller.default_config(**kargs)
        controller.update_fdr()
    else:
        model = ScopeData()
        controller = ScopeController(w, model, parameters)
        controller.default_config(**kargs)

    parameters.sigTreeStateChanged.connect(controller.parameter_change)

    w.show()
    sys.exit(app.exec_())
