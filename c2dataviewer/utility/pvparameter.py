# -*- coding: utf-8 -*-

"""
Copyright 2017 UChicago Argonne LLC
 as operator of Argonne National Laboratory

EPICS PV field parameters

"""
from collections import OrderedDict
from pyqtgraph.parametertree import Parameter
from pyqtgraph.parametertree import parameterTypes as pTypes
from pyqtgraph.python2_3 import asUnicode
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QWidget, QTreeView, QStandardItem, QStandardItemModel
from PyQt5.QtGui import QVBoxLayout


class FieldSelectWidget(QWidget):

    def __init__(self, data, fieldNameMap={}, parent=None):
        QWidget.__init__(self, parent)
        self.treeView = QTreeView()
        self.fieldNameMap = fieldNameMap
        self.fieldNameMap['None'] = 'None'

        self.model = QStandardItemModel()
        item = QStandardItem('None')
        self.model.appendRow(item)
        self.addItems(self.model, data)
        self.treeView.setModel(self.model)

        self.model.setHorizontalHeaderLabels([self.tr("Field Selection")])

        layout = QVBoxLayout()
        layout.addWidget(self.treeView)
        self.setLayout(layout)

        treeModel = self.treeView.selectionModel()
        treeModel.selectionChanged.connect(self.selectEvent)

    def addItem(self, parent, itemTuple):
        fieldLabel = str(itemTuple[0])
        fieldName = str(itemTuple[1])
        self.fieldNameMap[fieldLabel] = fieldName
        item = QStandardItem(str(fieldLabel))
        parent.appendRow(item)

    def addItems(self, parent, elements):

        for text, children in elements.items():
            if not children:
               continue
            if type(children) == type(OrderedDict()):
                label = str(text)
                if hasattr(children, 'title'):
                    label = str(children.title)
                item = QStandardItem(label)
                parent.appendRow(item)
                self.addItems(item, children)
            elif type(children) == list: #types.ListType:
                item = QStandardItem(str(text))
                parent.appendRow(item)
                for child in children:
                    self.addItem(item, child)
            else:
                self.addItem(parent, children)

    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def selectEvent(self, selected): #, deselected):
        index = selected.indexes()[0]
        item = self.model.itemFromIndex(index)
        itemData = self.model.itemData(index)
        fieldLabel = str(itemData[0])#.toPyObject())
        fieldName = self.fieldNameMap.get(fieldLabel)
        if fieldName:
            #self.pvFieldParameterItem.selectedFieldName = fieldName
            self.pvFieldParameterItem.setFieldName(fieldLabel)
            #self.pvFieldParameterItem.setFieldName(fieldName)
            #self.pvFieldParameterItem.setFieldLabel(fieldLabel)
            self.hide()


class PvFieldParameterItem(pTypes.WidgetParameterItem):
    MAX_COMBOBOX_HEIGHT = 20

    def __init__(self, param, depth):
        self.targetValue = None
        self.selectedFieldName = 'None'
        pTypes.WidgetParameterItem.__init__(self, param, depth)

    def makeWidget(self):
        opts = self.param.opts
        t = opts['type']

        arrayFieldDict = opts.get('arrayFieldDict')
        if arrayFieldDict:
            w = QtGui.QWidget()
            layout = QtGui.QHBoxLayout()
            w.setLayout(layout)
            self.button = QtGui.QPushButton('Select')
            layout.addWidget(self.button)
            layout.addStretch()
            self.button.clicked.connect(self.selectField)
            w.setValue = self.setFieldName
            w.value = self.getFieldName
            self.widget = w

            fieldNameMap = opts.get('fieldNameMap', {})
            self.fieldSelectWidget = FieldSelectWidget(data=arrayFieldDict, fieldNameMap=fieldNameMap)
            self.fieldSelectWidget.setWindowModality(Qt.ApplicationModal)
            self.fieldSelectWidget.pvFieldParameterItem = self
            self.fieldSelectWidget.resize(500, 300)
            w.sigChanged = self.fieldSelectWidget.treeView.selectionModel().selectionChanged
        else:
            w = QtGui.QComboBox()
            w.setMaximumHeight(self.MAX_COMBOBOX_HEIGHT)  ## set to match height of spin box and line edit
            w.sigChanged = w.currentIndexChanged
            w.value = self.value
            w.setValue = self.setValue
            self.widget = w
            self.limitsChanged(self.param, self.param.opts['limits'])
            if len(self.forward) > 0:
                self.setValue(self.param.value())
        return w

    def showFieldSelectWindow(self):
        self.fieldSelectWidget.show()

    def getFieldName(self):
        return self.selectedFieldName

    def setFieldName(self, fieldName):
        self.selectedFieldName = fieldName
        self.button.setText(fieldName)

    def setFieldLabel(self, fieldLabel):
        self.button.setText(fieldLabel)

    def selectField(self):
        self.fieldSelectWidget.show()

    def value(self):
        key = asUnicode(self.widget.currentText())
        return self.forward.get(key, None)

    def setValue(self, val):
        self.targetValue = val
        if val not in self.reverse[0]:
            self.widget.setCurrentIndex(0)
        else:
            key = self.reverse[1][self.reverse[0].index(val)]
            ind = self.widget.findText(key)
            self.widget.setCurrentIndex(ind)

    def limitsChanged(self, param, limits):
        # set up forward / reverse mappings for name:value

        if len(limits) == 0:
            limits = ['']  ## Can never have an empty list--there is always at least a singhe blank item.

        self.forward, self.reverse = PvFieldParameter.mapping(limits)
        try:
            self.widget.blockSignals(True)
            val = self.targetValue  # asUnicode(self.widget.currentText())

            self.widget.clear()
            for k in self.forward:
                self.widget.addItem(k)
                if k == val:
                    self.widget.setCurrentIndex(self.widget.count() - 1)
                    self.updateDisplayLabel()
        finally:
            self.widget.blockSignals(False)


class PvFieldParameter(Parameter):
    """

    """
    itemClass = PvFieldParameterItem

    GROUP_SIZE = 10

    def __init__(self, **opts):
        self.forward = OrderedDict()  # {name: value, ...}
        self.reverse = ([], [])  # ([value, ...], [name, ...])

        # Parameter uses 'limits' option to define the set of allowed values
        if 'fieldNameChoices' in opts:
            opts['limits'] = opts['fieldNameChoices']
        if opts.get('limits', None) is None:
            opts['limits'] = []
        Parameter.__init__(self, **opts)
        self.setLimits(opts['limits'])

    def setLimits(self, limits):
        """
        Override super class method.
        Set limits on the acceptable values for this parameter.
        The format of limits depends on the type of the parameter and
        some parameters do not make use of limits at all.
        """
        self.forward, self.reverse = self.mapping(limits)

        Parameter.setLimits(self, limits)
        if len(self.reverse[0]) > 0 and self.value() not in self.reverse[0]:
            self.setValue(self.reverse[0][0])

    @staticmethod
    def mapping(limits):
        # Return forward and reverse mapping objects given a limit specification
        forward = OrderedDict()  # {name: value, ...}
        reverse = ([], [])  # ([value, ...], [name, ...])
        if isinstance(limits, dict):
            for k, v in limits.items():
                forward[k] = v
                reverse[0].append(v)
                reverse[1].append(k)
        else:
            for v in limits:
                n = asUnicode(v)
                forward[n] = v
                reverse[0].append(v)
                reverse[1].append(n)
        return forward, reverse
