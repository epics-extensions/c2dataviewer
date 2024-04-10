# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Various custom UI components.
"""
import pyqtgraph as pg
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QPainter, QBrush, QPalette, QPen
from PyQt5.QtWidgets import QRubberBand, QWidget

class TransparentRubberBand(QRubberBand):
    def __init__(self, shape, parent):
        QRubberBand.__init__(self, shape, parent)

    def paintEvent(self, event):
        pal = QPalette()
        pal.setBrush(QPalette.Highlight, QBrush(Qt.black))
        self.setPalette(pal)
        pen = QPen()
        pen.setStyle(Qt.DashLine)
        pen.setColor(Qt.darkGreen)
        pen.setWidth(2)
        painter = QPainter(self)
        painter.setOpacity(1)
        painter.setPen(pen)
        rectangle = QRubberBand.geometry(self)
        rectangle2 = QRect(0,0,rectangle.width()-1, rectangle.height()-1)
        painter.drawRect(rectangle2)
        painter.end()

class RoiMidLines(QWidget):
    def __init__(self, xleft, yleft, xtop, ytop, parent=None):
        QWidget.__init__(self, parent)
        self.xleft = int(xleft)
        self.yleft = int(yleft)
        self.xtop = int(xtop)
        self.ytop = int(ytop)

    def paintEvent(self, event):
        pal = QPalette()
        pal.setBrush(QPalette.Highlight, QBrush(Qt.black))
        self.setPalette(pal)
        pen = QPen()
        pen.setStyle(Qt.DashLine)
        pen.setColor(Qt.darkGreen)
        pen.setWidth(2)
        painter = QPainter(self)
        painter.setPen(pen)
        painter.drawLine(0, self.yleft, self.xleft, self.yleft)
        painter.drawLine(self.xtop, 0, self.xtop, self.ytop)
        painter.end()
