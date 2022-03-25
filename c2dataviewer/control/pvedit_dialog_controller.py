import pyqtgraph
import random
from PyQt5 import QtGui
from PyQt5 import QtCore
from .pvconfig import PvConfig

def make_color_tuple(c):
    r = int(c[1:3], 16)
    g = int(c[3:5], 16)
    b = int(c[5:7], 16)

    return (r,g,b)

def make_color_hex(c):
    return '#%02x%02x%02x' % (c[0], c[1], c[2])

def randcolor():
    color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
    return make_color_tuple(color)

class PvEditDialogController:
    def __init__(self, widget, model, default_proto=None):
        self._win = widget
        self._model = model
        
        self._win.addPvButton.clicked.connect(self._on_addpv_click)
        self._win.buttonBox.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self._on_cancel)
        self._win.buttonBox.button(QtGui.QDialogButtonBox.Ok).clicked.connect(self._on_ok)

        self.callback = None
        self.protocol_list = None
        if default_proto is not None:
            self._win.protocolComboBox.setCurrentText(str(default_proto).lower())

        self._win.colorButton.setColor(randcolor())
            
    def set_completion_callback(self, callback):
        self.callback = callback
            
    def _on_addpv_click(self):
        pv_name = self._win.newPvLineEdit.text()
        proto = self._win.protocolComboBox.currentText()
        color = self._win.colorButton.color(mode='byte')
        self._add_pv(pv_name, color, proto)
        self._win.colorButton.setColor(randcolor())
        
    def _on_cancel(self):
        self._win.close()

    def _on_ok(self):
        pvlist = []
        for row in range(0, self._win.pvTableWidget.rowCount()):
            pvname = self._win.pvTableWidget.item(row, 0).text()
            proto = self._win.pvTableWidget.cellWidget(row, 1).currentText()
            color = make_color_hex(self._win.pvTableWidget.cellWidget(row, 2).color(mode='byte'))
            pvlist.append(PvConfig(pvname, color,proto))
        self.callback(pvlist)
        self._win.close()

    def _get_protocol_list(self):
        if self.protocol_list:
            return self.protocol_list

        self.protocol_list = []
        count = self._win.protocolComboBox.count()
        for i in range(count):
            self.protocol_list.append(self._win.protocolComboBox.itemText(i))
        return self.protocol_list
    
    def _add_pv(self, pvname, color, proto):
        rowcount = self._win.pvTableWidget.rowCount()
        self._win.pvTableWidget.setRowCount(rowcount + 1)

        #pvname edit
        item = QtGui.QTableWidgetItem(pvname)
        self._win.pvTableWidget.setItem(rowcount, 0, item)

        #protocol drop-down
        item = QtGui.QComboBox()
        item.addItems(self._get_protocol_list())
        item.setCurrentText(str(proto).lower())
        self._win.pvTableWidget.setCellWidget(rowcount, 1, item)

        #color button
        item = pyqtgraph.ColorButton(color=color)        
        self._win.pvTableWidget.setCellWidget(rowcount, 2, item)

        #remove button
        item = QtGui.QPushButton('Remove')
        def remove():
            row = self._win.pvTableWidget.indexAt(item.pos()).row();
            self._win.pvTableWidget.removeRow(row)
            
        item.clicked.connect(remove)
        self._win.pvTableWidget.setCellWidget(rowcount, 3, item)
        
    def show(self, pvlist):
        self._set_pvlist(pvlist)
        self._win.exec_()

    def _set_pvlist(self, pvlist):
        self._win.pvTableWidget.clearContents()
        self._win.pvTableWidget.setRowCount(0)
        
        for p in pvlist:
            self._add_pv(p.pvname, make_color_tuple(p.color), p.proto)
        
