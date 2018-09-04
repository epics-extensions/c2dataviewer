# -*- coding: utf-8 -*-

"""
Copyright 2017 UChicago Argonne LLC
 as operator of Argonne National Laboratory

"""

import numpy as np
import pyqtgraph as pg
from pyqtgraph import ptime
from PyQt5 import QtCore


class LivePlot:
    def __init__(self, win, pvaChannel, args, title=None, row=0, col=0, app=None, plots=None):
        """"""
        self.app = app
        self.args = args
        self.title = title
        self.row = row
        self.col = col
        self.fieldName = ['None'] * self.args["N_CHANNELS"]
        self.fieldEnable = [True] * self.args["N_CHANNELS"]
        for i, n in enumerate(self.args["FIELD"]):
            self.fieldName[i] = n

        self.win = win
        self.num_axes = 0
        self.autoScale = True
        self.lockAutoscale = False

        self.pvaChannel = pvaChannel

        self.trigmodes = {'auto': 1, 'single': 0, 'ext': 2}
        self.trigmode = self.trigmodes['auto']

        self.fps = None

        self.param_changed = False

        self.plots = plots

    def startProcess(self):
        """"""
        self.setupPlot(1)
        self.timer = QtCore.QTimer()
        self.timer.start(self.args["REFRESH_RATE"])
        self.timer.timeout.connect(self.update)
        self.lastTime = ptime.time()
        # signal generator, or qt QObject that emits signals on ext trig. like ca pv change.
        self.ext_trig_signal = self.pvaChannel.plot_signal_emitter

    # trig mode privide string, in self.treigmodes keys.
    def setTrigMode(self, tm):
        self.trigmode = self.trigmodes[tm]
        print ('setTrigMode %s' % (tm))

        try:
            self.timer.timeout.disconnect()
        except:
            pass

        if self.ext_trig_signal != None:
            try:
                self.ext_trig_signal.disconnect()
            except:
                pass

        if self.trigmode == self.trigmodes['auto']:
            self.timer.timeout.connect(self.update)
            print ('connect timer signal')


        elif self.trigmode == self.trigmodes['ext'] and self.ext_trig_signal != None:
            QtCore.QObject.connect(self.ext_trig_signal, QtCore.SIGNAL('my_signal()'), self.update)
            print ('connect ext signal')


    def deletePlot(self):

        print ('deletePlot')

        if self.plottype == 2:
            self.views[0].removeItem(self.curve[0])

            for nn in range(1, self.num_axes):
                self.views[nn].removeItem(self.curve[nn])
                self.plot.scene().removeItem(self.views[nn])
                self.plot.layout.removeItem(self.axes[nn])

            self.win.removeItem(self.plot)

        if self.plottype == 3:
            for nn in range(self.num_axes):
                self.views[nn].removeItem(self.curve[nn])
                self.win.removeItem(self.views[nn])

        if self.plottype == 4:
            for nn in range(self.num_axes):
                self.views[0].removeItem(self.curve[nn])

            self.win.removeItem(self.views[0])

        self.views = []
        self.axes = []
        self.num_axes = 0

    def doAutoRange(self):

        for v in self.views:
            v.autoRange()

    def setupPlot(self, num_axes_=None, is_log=False, is_singleaxis=False):
        # log not work on multi axis...
        if is_log or is_singleaxis:
            # self.setupPlot3(num_axes_,is_log)
            self.setupPlot4(num_axes_, is_log)
        else:
            self.setupPlot2(num_axes_, is_log)

    def setupPlot2(self, num_axes_=None, is_log=False):

        if num_axes_ == None:
            num_axes_ = self.num_axes

        print ('setupPlot %d' % num_axes_)


        self.is_log = is_log

        if self.num_axes > 0:
            self.deletePlot()

        self.plottype = 2

        self.num_axes = num_axes_

        self.plot = self.win.addPlot(title=self.title, row=self.row, col=self.col)
        self.views = []
        self.views.append(self.plot)
        self.axes = [self.plot.getAxis('left')]

        self.axes[0].setLabel('Channel 1', color=self.args["COLOR"][0])

        col_ = 3

        self.curve = []
        self.curve.append(self.plot.plot(pen=self.args["COLOR"][0]))

        for i in range(1, self.num_axes):
            print('1 setup view %d' % i)

            self.views.append(pg.ViewBox())
            self.axes.append(pg.AxisItem('right'))
            self.plot.layout.addItem(self.axes[i], 2, col_)
            col_ = col_ + 1
            self.plot.scene().addItem(self.views[i])

            self.axes[i].linkToView(self.views[i])
            self.views[i].setXLink(self.plot)
            self.axes[i].setLabel('Channel %d' % (i+1), color=self.args["COLOR"][i % len(self.args["COLOR"])])
            self.curve.append(pg.PlotCurveItem(pen=self.args["COLOR"][i % len(self.args["COLOR"])]))
            self.views[i].addItem(self.curve[i])

            print('2 setup view %d' % i)


        self.plot.vb.sigResized.connect(self.updateViews)

        self.updateViews()

        self.trigMarker = self.plot.plot(pen='r')

    def setupPlot3(self, num_axes_=None, is_log=False):

        if num_axes_ == None:
            num_axes_ = self.num_axes

        print ('setupPlot %d' % num_axes_)


        self.is_log = is_log

        if self.num_axes > 0:
            self.deletePlot()

        self.plottype = 3
        self.num_axes = num_axes_

        self.views = []
        self.axes = []
        self.curve = []
        self.row = 0
        self.col = 0
        for i in range(self.num_axes):
            self.plot = self.win.addPlot(title=self.title, row=self.row, col=self.col)
            self.views.append(self.plot)
            self.axes.append(self.plot.getAxis('left'))

            self.curve.append(self.plot.plot(pen=self.args.color[i]))
            self.axes[i].setLabel('Channel %d' % (i+1), color=self.args.color[i % len(self.args.color)])
            if self.is_log:
                self.plot.setLogMode(True, True)
            self.row = self.row + 1

        self.plot = self.views[0]

    def setupPlot4(self, num_axes_=None, is_log=False):

        if num_axes_ == None:
            num_axes_ = self.num_axes

        print ('setupPlot %d' % num_axes_)


        self.is_log = is_log

        if self.num_axes > 0:
            self.deletePlot()

        self.plottype = 4
        self.num_axes = num_axes_

        self.views = []
        self.axes = []
        self.curve = []
        self.row = 0
        self.col = 0
        self.plot = self.win.addPlot(title=self.title, row=self.row, col=self.col)
        if self.is_log:
            self.plot.setLogMode(True, True)
        self.views.append(self.plot)
        self.axes.append(self.plot.getAxis('left'))
        for i in range(self.num_axes):
            self.curve.append(self.plot.plot(pen=self.args["COLOR"][i]))
            self.col = self.col + 1

        self.plot = self.views[0]

    def updateViews(self):

        nplots = len(self.views)

        for nn in range(1, nplots):
            self.views[nn].setGeometry(self.plot.vb.sceneBoundingRect())
            self.views[nn].linkedViewChanged(self.plot.vb, self.views[nn].XAxis)

    def filter(self, d, t=None):
        rd, rt = d, t
        if self.args["MAX"] is not None:
            mask = rd <= self.args["MAX"]
            rd = rd[mask]
            if t is not None:
                rt = rt[mask]
        if self.args["MIN"] is not None:
            mask = rd >= self.args["MIN"]
            rd = rd[mask]
            if t is not None:
                rt = rt[mask]
        if t is not None:
            return rd, rt
        return rd

    def setFieldName(self, n, newFieldName):
        self.fieldName[n] = newFieldName
        self.pvaChannel.restartMonitor(self.fieldName)

    def setFieldEnable(self, n, enable):
        self.fieldEnable[n] = enable

    def drawCurveXY(self, curve, fieldNameX, fieldNameY, enabled, is_drawtrigmark=False):
        if not enabled or not fieldNameX or str(fieldNameX) == 'None':
            curve.clear()
            return
        if not enabled or not fieldNameY or str(fieldNameY) == 'None':
            curve.clear()
            return

        self.pvaChannel.wait()
        dx = None
        dy = None
        try:
            dx = self.pvaChannel.getFieldData(fieldNameX)
            dy = self.pvaChannel.getFieldData(fieldNameY)
        except KeyError:
            # should use log instead of print to console.
            # to be improve during next code refractoring
            print("Either given key (%s, %s) does not exit, or data is empty" % fieldNameX, fieldNameY)
            curve.clear()
            self.pvaChannel.signal()
            return
        if dx is None or dy is None:
            curve.clear()
            self.pvaChannel.signal()
            return

        N = len(dx)
        Ny = len(dy)

        self.pvaChannel.signal()

        dx = self.filter(dx)
        dy = self.filter(dy)
        # the following is moved out of else... START
        curve.setData(dx, dy)

    def drawCurve(self, curve, fieldName, enabled, is_drawtrigmark=False):
        if not enabled or not fieldName or str(fieldName) == 'None':
            curve.clear()
            return
        self.pvaChannel.wait()
        d = None
        try:
            d = self.pvaChannel.getFieldData(fieldName)
        except KeyError:
            # should use log instead of print to console.
            # to be improve during next code refractoring
            print("Either given key (%s) does not exit, or data is empty" % fieldName)
            curve.clear()
            self.pvaChannel.signal()
            return
        if d is None:
            curve.clear()
            self.pvaChannel.signal()
            return

        N = len(d)
        # in case on time reference in PV, we declare T to sec per sample.
        # also f is sample ratge of 1samp/sec
        # sample period
        T = 1.0
        # sample frequecy
        f = 1.0
        # time array
        t = None
        # if we have a sample rate in pv, use it for time reference
        if self.args["FREQ_FIELD"]:
            f = self.pvaChannel.getFieldData(self.args.freqField)
            if f <= 0.0: return
            T = 1.0 / f
            # print('Used freqField')
        # if pv has a sample period, us it for time reference.
        elif self.args["PERIOD_FIELD"]:
            T = self.pvaChannel.getFieldData(self.args["PERIOD_FIELD"])
            # print('Used sampPeriodField')
        # calc the sample period from Time vector.
        elif self.args["TIME_FIELD"]:
            t = self.pvaChannel.getFieldData(self.args["TIME_FIELD"])
            if t is not None:
                if N != len(t): return
                T = np.diff(t).mean()
                # print('Used timeField')

        self.pvaChannel.signal()

        if self.args["ALGORITHM"] == "DIFF":
            d = np.diff(d)

        if self.args["ALGORITHM"] == "FFT" or self.args["ALGORITHM"] == "PSD":
            if N == 0: return
            # yf = scipy.fftpack.rfft(d)
            # xf = scipy.fftpack.rfftfreq(N, d=T)
            yf = np.fft.rfft(d)
            xf = np.fft.rfftfreq(N, d=T)

        if self.args['HISTOGRAM'] and not self.args["ALGORITHM"] == "PSD" and not self.args["ALGORITHM"] == "FFT":
            curve.opts['stepMode'] = True
            # curve.setFillLevel(0)
            # curve.setFillBrush('y')
        else:
            curve.opts['stepMode'] = False
            # curve.setFillLevel(None)
            # curve.setFillBrush(None)

        if self.args["ALGORITHM"] == "FFT":
            curve.setData(xf, (2. / N) * np.abs(yf))
        elif self.args["ALGORITHM"] == "PSD":
            df = np.diff(xf).mean()
            psd = ((2.0 / N * np.abs(yf)) ** 2) / df / 2
            curve.setData(xf, psd)
        elif self.args['HISTOGRAM'] and not self.args["ALGORITHM"] == "PSD" and not self.args["ALGORITHM"] == "FFT":
            d = self.filter(d)
            y, x = np.histogram(d, bins=self.args["N_BINS"])
            curve.setData(x, y)
        else:
            d = self.filter(d)
            # what was this for??? what does pvtrigger name have to do with time reference?
            # !!if self.pvaChannel.pvtrigger_name is None:
            # !!    curve.setData(d)
            # !!else:
            # the following is moved out of else... START
            if t is None:
                t = np.arange(len(d)) * T
            try:
                firsttime = t[0]
            except IndexError:
                return
            curve.setData(t - firsttime, d)

            if self.pvaChannel.trigger_mode and self.pvaChannel.is_triggered and is_drawtrigmark:
                marktime = self.pvaChannel.trigger_timestamp - firsttime
                marklinex = np.array([marktime, marktime])
                markliney = np.array([1.2 * max(d), 0.8 * min(d)])
                self.trigMarker.setData(marklinex, markliney)
            else:
                # !!if self.pvaChannel.trigger_mode == False and is_drawtrigmark:
                self.trigMarker.clear()
                # above moved out of else- END

    def update(self):

        # check to see which fields are enabled, that is not NONE
        # set number of axes to match.

        if self.param_changed:
            naxes = 1
            for i in range(0, len(self.fieldName)):
                if self.fieldName[i] != 'None':
                    naxes = i + 1
            is_log = self.args["ALGORITHM"] in ["FFT", "PSD"]

            # if user changed number of curves enabled in gui, we give the cuirve an axis
            if self.args["ALGORITHM"] == "XvsY":
                self.setupPlot(naxes, is_log, True)
            else:
                self.setupPlot(naxes, is_log, False)

        self.param_changed = False

        if self.args["ALGORITHM"] != "XvsY":
            for i in range(0, len(self.fieldName)):
                if self.fieldName[i] != 'None':
                    if self.pvaChannel.pvtrigger_name is None:
                        self.drawCurve(self.curve[i], self.fieldName[i], self.fieldEnable[i])
                    else:
                        # draw all curves, for i==0 also draw the trigger marker
                        self.drawCurve(self.curve[i], self.fieldName[i], self.fieldEnable[i], i == 0)
        else:
            if self.fieldName[0] != 'None' and self.fieldName[1] != 'None':
                self.drawCurveXY(
                    self.curve[0],
                    self.fieldName[0],
                    self.fieldName[1],
                    self.fieldEnable[0] and self.fieldEnable[1])
                self.curve[1].clear()

            if self.fieldName[2] != 'None' and self.fieldName[3] != 'None':
                self.drawCurveXY(
                    self.curve[2],
                    self.fieldName[2],
                    self.fieldName[3],
                    self.fieldEnable[2] and self.fieldEnable[3])
                self.curve[3].clear()

        if self.autoScale:
            self.doAutoRange()
            self.autoScale = False

        if self.lockAutoscale:
            self.doAutoRange()

        # update fps statistics
        now = ptime.time()
        dt = now - self.lastTime
        self.lastTime = now
        if self.fps is None:
            self.fps = 1.0 / dt
        else:
            s = np.clip(dt * 3., 0, 1)
            self.fps = self.fps * (1 - s) + (1.0 / dt) * s
        self.app.processEvents()  # force complete redraw for every plot

    def addPlot(self, row=0, col=0, title=None):
        # self.initProcess()
        tmp = LivePlot(self.win,
                 self.pvaChannel,
                 self.args,
                 title=title,
                 row=row,
                 col=col,
                 app=self.app)
        tmp.startProcess()
        self.plots.append(tmp)
