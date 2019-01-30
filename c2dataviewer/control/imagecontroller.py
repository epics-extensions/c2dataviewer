# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""


import pyqtgraph.ptime as ptime

class ImageController:
    def __init__(self, widget, **kargs):
        """

        :param widget:
        :param kargs:
        """
        self._win = widget
        if self._win is None:
            raise RuntimeError("Widget is unknown")

        self._cameras = kargs.get("PV", None)
        if self._cameras is None:
            raise RuntimeError("EPICS PV for camera is unknown")

        self.datareceiver = kargs.get('data', None)

        self._win.pvPrefix.addItems(self._cameras)
        self._win.pvPrefix.currentIndexChanged.connect(lambda: self.camera_changed())

        self._dlg = kargs.get("LIMIT", None)
        self._warning = kargs.get("WARNING", None)

        self._lastFrames = 0
        self._lastTime = None
        self._fps = 0.0
        self._net = 0.0
        self._lastMbReceived = 0

        # Gain control and adjust
        self._win.imageBlackSlider.valueChanged.connect(lambda: self.black_changed())
        self._win.imageGainSlider.valueChanged.connect(lambda: self.gain_changed())
        self._win.imageAutoAdjust.clicked.connect(lambda: self.auto_gain_cal())
        self._win.imageBlackSlider.setMinimum(0)
        self._win.imageGainSlider.setMaximum(40960)
        self._win.imageGainSlider.setMinimum(1)

        # Frame DAQ control
        self._framerates = {'1 Hz': 1, '2 Hz': 2, '5 Hz': 5, '10 Hz': 10, 'Full IOC Rate': -1}
        self._win.iocRate.addItems(self._framerates.keys())
        self._win.iocRate.setCurrentIndex(2)
        self._win.iocRate.currentIndexChanged.connect(lambda: self.frameRateChanged())

        # # Limit control to avoid overflow network for best performance
        self._dlg.deadPxLimit.setText(str(self._win.imageWidget._pref["DPXLimit"]))
        self._dlg.cpuLimit.setText(str(self._win.imageWidget._pref["CPULimit"]))
        self._dlg.netLimit.setText(str(self._win.imageWidget._pref["NetLimit"]))

        # Adjust limits panel
        self._win.adjustLimits.clicked.connect(lambda: self.adjustLimits())

        self._dlg.okButton.clicked.connect(lambda: self.acceptNewLimits())
        self._dlg.cancelButton.clicked.connect(lambda: self.cancelNewLimits())

        self._warning.warningConfirmButton.clicked.connect(lambda: self.acceptWarning())

        self._lastTime = ptime.time()
        self._timer = kargs.get("timer", None)
        if self._timer is None:
            raise RuntimeError("No valid timer")
        self._timer.timeout.connect(self.updateStatus)
        self._timer.start(1000)

        self.frameRateChanged()

    def black_changed(self):
        """

        :return:
        """
        try:
            self._win.imageWidget.set_black(self._win.imageBlackSlider.value())
        except:
            pass

    def gain_changed(self):
        """

        :return:
        """
        try:
            self._win.imageWidget.set_gain(self._win.imageGainSlider.value() / 10.0)
        except:
            pass

    def auto_gain_cal(self):
        """

        :return:
        """
        self._win.imageWidget.enable_auto_gain()

    def frameRateChanged(self):
        """

        :return:
        """
        n = self._win.iocRate.currentIndex()
        self.resetStatus()
        fr = list(self._framerates.keys())[n]
        try:
            self._win.imageWidget.set_framerate(self._framerates[fr])
        except NameError:
            pass

    def adjustLimits(self):
        """

        :return:
        """
        self._dlg.exec_()

    def __update_limits(self, key, value):
        """

        :param field:
        :param value:
        :return:
        """
        try:
            self._win.imageWidget._pref[key] = float(value.text())
        except ValueError:
            value.setText(str(self._win.imageWidget._pref[key]))

    def acceptNewLimits(self):
        """

        :return:
        """
        self.__update_limits("DPXLimit", self._dlg.deadPxLimit)
        self.__update_limits("CPULimit", self._dlg.cpuLimit)
        self.__update_limits("NetLimit", self._dlg.netLimit)

        self._dlg.close()

    def cancelNewLimits(self):
        """

        :return:
        """
        self._dlg.reject()

    def acceptWarning(self):
        """

        :return:
        """
        self._warning.close()

    def camera_changed(self):
        """

        :param value:
        :return:
        """

        n = self._win.pvPrefix.currentIndex()
        self.resetStatus()
        #
        try:
            self._win.imageWidget.camera_changed(self._cameras[n])
        except ValueError:
            if self._warning is not None:
                self._warning.warningTextBrowse.setText("No data from: {}. Stop image display".
                                                        format(self._cameras[n]))
                self._warning.show()

    def resetStatus(self):
        """

        :return:
        """
        self._win.imageWidget._df = [0]
        self._win.imageWidget._db = [0]
        self._win.imageWidget._dt = [1]
        self._fps = 0
        self._net = 0
        # TODO clear window status
        # try:
        #     self._win.clearStatus()
        # except NameError:
        #     pass

    def statistics_update(self, valuefield, value, **kargs):
        """

        :param valuefield:
        :param value:
        :param kargs:
        :return:
        """
        fmt = kargs.get('fmt', '%.1f')
        hilimit = kargs.get('hilimit', None)
        lolimit = kargs.get('lowlimit', None)
        callback = kargs.get('callback', False)

        valuefield.setText(str(fmt) % value)
        if hilimit is not None and value > hilimit:
            valuefield.setStyleSheet('color: red; font-weight: bold')
            if callback:
                self.throttleBack()
        elif lolimit is not None and value < lolimit:
            valuefield.setStyleSheet('color: red; font-weight: bold')
            if callback:
                self.throttleBack()
        else:
            valuefield.setStyleSheet('color: black; font-weight: normal')

    def throttleBack(self):
        """

        :return:
        """
        selected = self._win.iocRate.currentIndex()
        newChoice = selected - 1
        if newChoice >= 0:
            self._win.iocRate.setCurrentIndex(newChoice)
            self.frameRateChanged()
            # self._win.setStatus('Requested frame rate reduced -- %s limit exceeded.' % sender.name)

    def updateStatus(self):
        """

        :return:
        """
        now = ptime.time()

        df = self._win.imageWidget.framesDisplayed - self._lastFrames
        db = self._win.imageWidget.mbReceived - self._lastMbReceived
        self._lastFrames = self._win.imageWidget.framesDisplayed
        self._lastMbReceived = self._win.imageWidget.mbReceived

        dt = now - self._lastTime
        self._lastTime = now

        self._win.imageWidget._df.append(df)
        self._win.imageWidget._df = self._win.imageWidget._df[-3:]
        self._win.imageWidget._db.append(db)
        self._win.imageWidget._db = self._win.imageWidget._db[-3:]
        self._win.imageWidget._dt.append(dt)
        self._win.imageWidget._dt = self._win.imageWidget._dt[-3:]

        try:
            self._fps = sum(self._win.imageWidget._df) / sum(self._win.imageWidget._dt)
        except:
            self._fps = 0
        try:
            self._net = sum(self._win.imageWidget._db) / sum(self._win.imageWidget._dt)
        except:
            self._net = 0

        with self._win._proc.oneshot():
            cpu = self._win._proc.cpu_percent(None)

        self.statistics_update(self._win.frameRate, self._fps,
                               lolimit=self._win.imageWidget._pref['FPSLimit'])
        self.statistics_update(self._win.maxPixel, max(self._win.imageWidget._max), fmt='%.0f')
        self.statistics_update(self._win.minPixel, max(self._win.imageWidget._min), fmt='%.0f')
        self.statistics_update(self._win.deadPixel, max(self._win.imageWidget._dpx), fmt='%.0f',
                               hilimit=self._win.imageWidget._pref["DPXLimit"])
        self.statistics_update(self._win.cpuUsage, cpu,
                               hilimit=self._win.imageWidget._pref['CPULimit'],
                               callback=True)
        self.statistics_update(self._win.netLoad, self._net, fmt='%.0f',
                               hilimit=self._win.imageWidget._pref['NetLimit'],
                               callback=True)
