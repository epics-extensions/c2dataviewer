# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""
import datetime
import pyqtgraph.ptime as ptime


class ImageController:

    SLIDER_MAX_VAL = 1_000_000_000
    SLIDER_MIN_VAL = -SLIDER_MAX_VAL
    SPINNER_MAX_VAL = 1.7976931348623157e+308
    SPINNER_MIN_VAL = -SPINNER_MAX_VAL

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
        self._blackWhiteDlg = kargs.get("BLACKWHITELIMIT", None)
        self._warning = kargs.get("WARNING", None)

        self._lastFrames = 0
        self._lastTime = None
        self._fps = 0.0
        self._net = 0.0
        self._lastMbReceived = 0

        # GUI styles
        self._inputTypeDefaultStyle = self._win.lblValidInput.styleSheet()

        # Image and zoom
        self._win.lblXsize.setToolTip("Number of pixels image has in X direction. \nIf ROI is selected, numbers in parentheses \nshow the range of displayed pixels.")
        self._win.lblYsize.setToolTip("Number of pixels image has in Y direction. \nIf ROI is selected, numbers in parentheses \nshow the range of displayed pixels.")
        self._win.resetZoomButton.clicked.connect(lambda: self._callback_reset_zoom_button())

        # Black control
        self._win.imageBlackSlider.valueChanged.connect(lambda: self._callback_black_changed_slider())
        self._win.imageBlackSpinBox.valueChanged.connect(lambda: self._callback_black_changed_spin())
        self.changeimageBlackLimits(0, self.SLIDER_MAX_VAL)
        self._imageBlackSliderFactor = 1
        self._win.imageWidget.set_BlackLimitsCallback(self.changeimageBlackLimits)
        self._win.imageWidget.set_BlackCallback(self.updateGuiBlack)

        # White control
        self._win.imageWhiteSlider.valueChanged.connect(lambda: self._callback_white_changed_slider())
        self._win.imageWhiteSpinBox.valueChanged.connect(lambda: self._callback_white_changed_spin())
        self.changeimageWhiteLimits(1, self.SLIDER_MAX_VAL)
        self._imageWhiteSliderFactor = 1
        self._win.imageWidget.set_WhiteLimitsCallback(self.changeimageWhiteLimits)
        self._win.imageWidget.set_WhiteCallback(self.updateGuiWhite)

        # Auto adjust black/white
        self._win.imageAutoAdjust.clicked.connect(lambda: self.auto_levels_cal())
        self._win.imageWidget.set_getBlackWhiteLimits(self.getimageBlackLimits, self.getimageWhiteLimits)

        # Set limits on the dialog widgets
        self._blackWhiteDlg.blackMin.setMinimum(self.SPINNER_MIN_VAL)
        self._blackWhiteDlg.blackMin.setMaximum(self.SPINNER_MAX_VAL)
        self._blackWhiteDlg.blackMax.setMinimum(self.SPINNER_MIN_VAL)
        self._blackWhiteDlg.blackMax.setMaximum(self.SPINNER_MAX_VAL)
        self._blackWhiteDlg.whiteMin.setMinimum(self.SPINNER_MIN_VAL)
        self._blackWhiteDlg.whiteMin.setMaximum(self.SPINNER_MAX_VAL)
        self._blackWhiteDlg.whiteMax.setMinimum(self.SPINNER_MIN_VAL)
        self._blackWhiteDlg.whiteMax.setMaximum(self.SPINNER_MAX_VAL)

        # Adjust limits for black and white
        self._win.imageLimitsAdjust.clicked.connect(lambda: self._callback_adjustBlackWhiteLimits())
        self._blackWhiteDlg.okButton.clicked.connect(lambda: self._callback_acceptNewBlackWhiteLimits())
        self._blackWhiteDlg.cancelButton.clicked.connect(lambda: self._callback_cancelNewBlackWhiteLimits())

        # Frame DAQ control
        self._framerates = {'1 Hz': 1, '2 Hz': 2, '5 Hz': 5, '10 Hz': 10, 'Full IOC Rate': -1}
        self._win.iocRate.addItems(self._framerates.keys())
        self._win.iocRate.setCurrentIndex(2)
        self._win.iocRate.currentIndexChanged.connect(lambda: self.frameRateChanged())

        # # Limit control to avoid overflow network for best performance
        text = self._win.imageWidget._pref["DPXLimit"] or ''
        self._dlg.deadPxLimit.setText(str(text))

        text = self._win.imageWidget._pref["CPULimit"] or ''
        self._dlg.cpuLimit.setText(str(text))

        text = self._win.imageWidget._pref["NetLimit"] or ''
        self._dlg.netLimit.setText(str(text))

        # Add tooltips for statistics
        self._win.maxPixel.setToolTip("Maximum value in the image. \nIf ROI is selected, value in the \nparentheses apply for the displayed area.")
        self._win.minPixel.setToolTip("Minimum value in the image. \nIf ROI is selected, value in the \nparentheses apply for the displayed area.")
        self._win.deadPixel.setToolTip("Number of pixels that exceed \nthe dead pixel threshold. \nIf ROI is selected, value in the \nparentheses apply for the displayed area.")

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
        self._startTime = ptime.time()

    def _callback_black_changed_slider(self):
        """
        This callback is called when user change the value on the "black" slider.

        :return:
        """
        try:
            black = self._win.imageBlackSlider.value() / self._imageBlackSliderFactor
            self._win.imageWidget.set_black(black)
            self._win.imageBlackSpinBox.blockSignals(True)
            self._win.imageBlackSpinBox.setValue(black)
            self._win.imageBlackSpinBox.blockSignals(False)
        except:
            pass
        self._win.imageBlackSlider.blockSignals(False)

    def _callback_black_changed_spin(self):
        """
        This callback is called when user change the value on the "black" spinner.

        :return:
        """
        try:
            black = self._win.imageBlackSpinBox.value()
            self._win.imageWidget.set_black(black)
            self._win.imageBlackSlider.blockSignals(True)
            self._win.imageBlackSlider.setValue(black * self._imageBlackSliderFactor)
            self._win.imageBlackSlider.blockSignals(False)
        except:
            pass

    def _callback_white_changed_slider(self):
        """
        This callback is called when user change the value on the "white" slider.

        :return:
        """
        try:
            white = self._win.imageWhiteSlider.value() / self._imageWhiteSliderFactor
            self._win.imageWidget.set_white(white)
            self._win.imageWhiteSpinBox.blockSignals(True)
            self._win.imageWhiteSpinBox.setValue(white)
            self._win.imageWhiteSpinBox.blockSignals(False)
        except:
            pass

    def _callback_white_changed_spin(self):
        """
        This callback is called when user change the value on the "white" spinner.

        :return:
        """
        try:
            white = self._win.imageWhiteSpinBox.value()
            self._win.imageWidget.set_white(white)
            self._win.imageWhiteSlider.blockSignals(True)
            self._win.imageWhiteSlider.setValue(white * self._imageWhiteSliderFactor)
            self._win.imageWhiteSlider.blockSignals(False)

        except:
            pass

    def _callback_reset_zoom_button(self):
        """
        This callback is called when user click on the "Reset Zoom" button.

        :return:
        """
        self._win.imageWidget.reset_zoom()

    def auto_levels_cal(self):
        """

        :return:
        """
        self._win.imageWidget.enable_auto_white()

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

    def _callback_adjustBlackWhiteLimits(self):
        """
        This callback is called when user press the "Adjust limits" in the Image Adjustment section.
        It will open the pop screen which allow to change the min and the max values for the
        black and white slider/spinner box.

        :return:
        """
        # Set current values
        self._blackWhiteDlg.blackMin.setValue(self._win.imageBlackSpinBox.minimum())
        self._blackWhiteDlg.blackMax.setValue(self._win.imageBlackSpinBox.maximum())
        self._blackWhiteDlg.whiteMin.setValue(self._win.imageWhiteSpinBox.minimum())
        self._blackWhiteDlg.whiteMax.setValue(self._win.imageWhiteSpinBox.maximum())

        # Launch the dialog
        self._blackWhiteDlg.exec_()


    def _callback_acceptNewBlackWhiteLimits(self):
        """
        This callback is called when the user confirms the new limits for the black and the white limits.

        :return:
        """
        self.changeimageBlackLimits(self._blackWhiteDlg.blackMin.value(),
                                    self._blackWhiteDlg.blackMax.value())
        self.changeimageWhiteLimits(self._blackWhiteDlg.whiteMin.value(),
                                   self._blackWhiteDlg.whiteMax.value())
        self._blackWhiteDlg.close()

    def _callback_cancelNewBlackWhiteLimits(self):
        """
        This callback is called when user cancels the new limits for the black and the white limits.

        :return:
        """
        self._blackWhiteDlg.reject()

    def __update_limits(self, key, value):
        """

        :param field:
        :param value:
        :return:
        """
        try:
            if value.text():
                self._win.imageWidget._pref[key] = float(value.text())
            else:
                self._win.imageWidget._pref[key] = None
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
        try:
            self._win.imageWidget.camera_changed(self._cameras[n])
        except (ValueError, RuntimeError):
            if self._warning is not None:
                self._warning.warningTextBrowse.setText("No data from: {}. Stop image display. \n"
                                                        "Please select a different channel.".
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

    def statistics_update(self, valuefield, value, **kargs):
        """
        Update widget with a new value on the GUI. If limits are specified and value is outside them, text on the widget
        will become red.

        :param valuefield: (QWidget) Widget where status should be writen. It must support "setText" and  "setStyleSheet" methods.
        :param value: (Object or Tuple/List of objects) Value which should be written to the widget. Multiple values can be passed as
                        tuple or array. If this is the case, **kargs must contain a formatting string that supports supplied number of values.
        :param kargs: (dict) Following keyword parameters are supported:
                                * "fmt" - (str) Formating string. Default value is "%.1f".
                                * "hilimit"  - (number) High limit. If the max value exceeds this value, text on the widget will become bold and red. Default is None.
                                * "lowlimit" - (number) Low limit. If the min value is less than this value, text on the widget will become bold and red. Default is None.
                                * "callback" - (bool) If this is the True and high or low limits are reached, *throttleBack* method is called. The default value is False.
        :return:
        """
        fmt = kargs.get('fmt', '%.1f')
        hilimit = kargs.get('hilimit', None)
        lolimit = kargs.get('lowlimit', None)
        callback = kargs.get('callback', False)

        valuefield.setText(str(fmt) % value)
        maxValue = max(value) if isinstance(value, (list, tuple)) else value
        minValue = min(value) if isinstance(value, (list, tuple)) else value
        if hilimit is not None and maxValue > hilimit:
            valuefield.setStyleSheet('color: red; font-weight: bold')
            if callback:
                self.throttleBack()
        elif lolimit is not None and minValue < lolimit:
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
        runtime = now-self._startTime

        isZoomedImage = self._win.imageWidget.is_zoomed()
        xOffset, yOffset, width, height = self._win.imageWidget.get_zoom_region()

        zoomMsg = ""
        zoomMsgStyle = "color: black"
        if (isZoomedImage and width == self._win.imageWidget.ZOOM_LENGTH_MIN
                          and height == self._win.imageWidget.ZOOM_LENGTH_MIN):
            zoomMsg = "Maximum zoom reached"
            zoomMsgStyle = "color: red"
        elif isZoomedImage and width == self._win.imageWidget.ZOOM_LENGTH_MIN:
            zoomMsg = "Maximum zoom in X direction reached"
            zoomMsgStyle = "color: red"
        elif isZoomedImage and height == self._win.imageWidget.ZOOM_LENGTH_MIN:
            zoomMsg = "Maximum zoom in Y direction reached"
            zoomMsgStyle = "color: red"
        self._win.zoomStatusLabel.setText(zoomMsg)
        self._win.zoomStatusLabel.setStyleSheet(zoomMsgStyle)

        df = self._win.imageWidget.framesDisplayed - self._lastFrames
        db = self._win.imageWidget.mbReceived - self._lastMbReceived
        self._lastFrames = self._win.imageWidget.framesDisplayed
        self._lastMbReceived = self._win.imageWidget.mbReceived
        averageFrameRate = self._win.imageWidget.framesDisplayed/runtime

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

        self._win.lblValidInput.setText(self._win.imageWidget._inputType + " "  + ("" if self._win.imageWidget._isInputValid else "(Invalid)"))
        if self._win.imageWidget._isInputValid:
            self._win.lblValidInput.setStyleSheet(self._inputTypeDefaultStyle)
        else:
            self._win.lblValidInput.setStyleSheet('background-color : red;')

        self._win.runtime.setText(str(datetime.timedelta(seconds=round(runtime))))
        self._win.setStyleSheet('color: black; font-weight: normal')
        self.statistics_update(self._win.nFrames, self._win.imageWidget.framesDisplayed, fmt='%d')
        self.statistics_update(self._win.averageFrameRate, averageFrameRate, fmt='%.1f')
        self.statistics_update(self._win.frameRate, self._fps,
                               lolimit=self._win.imageWidget._pref['FPSLimit'])

        if isZoomedImage:
            values = (self._win.imageWidget._max[-1], self._win.imageWidget._maxRoi[-1])
            fmt = '%.0f (%.0f)'
        else:
            values = (self._win.imageWidget._max[-1])
            fmt = '%.0f'
        self.statistics_update(self._win.maxPixel, values, fmt=fmt)

        if isZoomedImage:
            values = (self._win.imageWidget._min[-1], self._win.imageWidget._minRoi[-1])
            fmt = '%.0f (%.0f)'
        else:
            values = (self._win.imageWidget._min[-1])
            fmt = '%.0f'
        self.statistics_update(self._win.minPixel, values, fmt=fmt)

        if isZoomedImage:
            values = (max(self._win.imageWidget._dpx), max(self._win.imageWidget._dpxRoi))
            fmt = '%.0f (%.0f)'
        else:
            values = (max(self._win.imageWidget._dpx))
            fmt = '%.0f'
        self.statistics_update(self._win.deadPixel, values, fmt=fmt,
                                hilimit=self._win.imageWidget._pref["DPXLimit"])

        self.statistics_update(self._win.cpuUsage, cpu,
                               hilimit=self._win.imageWidget._pref['CPULimit'],
                               callback=True)
        self.statistics_update(self._win.netLoad, self._net, fmt='%.0f',
                               hilimit=self._win.imageWidget._pref['NetLimit'],
                               callback=True)

        # Update image and zoom section
        self._win.lblXsize.setText(' '.join([str(self._win.imageWidget.x),
                '' if not isZoomedImage else f"({xOffset}-{xOffset+width})"
                                            ]))
        self._win.lblYsize.setText(' '.join([str(self._win.imageWidget.y),
                '' if not isZoomedImage else f"({yOffset}-{yOffset+height})"
                                            ]))

    def changeimageBlackLimits(self, minVal, maxVal):
        """
        Set the minimum and the maximum for the black settings widgets (slider and the spinner).
        If the value is too big or too small for the slider, factor will be calculated, by which
        the value is multiplied/divided.

        :param minVal: (Number) Minimum possible setting for the slider and the spinner.
        :param maxVal: (Number) Maximum possible setting for the slider and the spinner.
        :return:
        """
        sliderFactor = 1
        if (maxVal > self.SLIDER_MAX_VAL or minVal < self.SLIDER_MIN_VAL):
            sliderFactor = max(self.SLIDER_MIN_VAL / minVal if minVal != 0 else 0,
                               self.SLIDER_MAX_VAL / maxVal if maxVal != 0 else 0,)

        self._imageBlackSliderFactor = sliderFactor
        self._win.imageBlackSlider.setMinimum(minVal * sliderFactor)
        self._win.imageBlackSlider.setMaximum(maxVal * sliderFactor)

        self._win.imageBlackSpinBox.setMinimum(minVal)
        self._win.imageBlackSpinBox.setMaximum(maxVal)

    def getimageBlackLimits(self):
        """
        Get the current settings for the black limits.

        :return: (Number, Number) Tuple of min and max values.
        """
        return (self._win.imageBlackSpinBox.minimum(),
                self._win.imageBlackSpinBox.maximum())

    def changeimageWhiteLimits(self, minVal, maxVal):
        """
        Set the minimum and the maximum for the black settings widgets (slider and the spinner).
        If the value is too big or too small for the slider, factor will be calculated, by which
        the value is multiplied/divided.

        :param minVal: (Number) Minimum possible setting for the slider and the spinner.
        :param maxVal: (Number) Maximum possible setting for the slider and the spinner.
        :return:
        """
        sliderFactor = 1
        if (maxVal > self.SLIDER_MAX_VAL or minVal < self.SLIDER_MIN_VAL):
            sliderFactor = max(self.SLIDER_MIN_VAL / minVal if minVal != 0 else 0,
                               self.SLIDER_MAX_VAL / maxVal if maxVal != 0 else 0,)

        self._imageWhiteSliderFactor = sliderFactor
        self._win.imageWhiteSlider.setMinimum(minVal * sliderFactor)
        self._win.imageWhiteSlider.setMaximum(maxVal * sliderFactor)

        self._win.imageWhiteSpinBox.setMinimum(minVal)
        self._win.imageWhiteSpinBox.setMaximum(maxVal)

    def getimageWhiteLimits(self):
        """
        Get the current settings for the white limits.

        :return: (Number, Number) Tuple of min and max values.
        """
        return (self._win.imageWhiteSpinBox.minimum(),
                self._win.imageWhiteSpinBox.maximum())

    def updateGuiBlack(self, value):
        """
        Update values on the black slider and spinner.

        :param value: (Number) Value to be set to the black slider and spinner.
        :return:
        """
        # Update the text spinner
        self._win.imageBlackSpinBox.blockSignals(True)
        self._win.imageBlackSpinBox.setValue(value)
        self._win.imageBlackSpinBox.blockSignals(False)

        self._win.imageBlackSlider.blockSignals(True)
        self._win.imageBlackSlider.setValue(value * self._imageBlackSliderFactor)
        self._win.imageBlackSlider.blockSignals(False)

    def updateGuiWhite(self, value):
        """
        Update values on the white slider and spinner.

        :param value: (Number) Value to be set to the white slider and spinner.
        :return:
        """
        # Update the text spinner
        self._win.imageWhiteSpinBox.blockSignals(True)
        self._win.imageWhiteSpinBox.setValue(value)
        self._win.imageWhiteSpinBox.blockSignals(False)

        # Update the slider
        self._win.imageWhiteSlider.blockSignals(True)
        self._win.imageWhiteSlider.setValue(value * self._imageWhiteSliderFactor)
        self._win.imageWhiteSlider.blockSignals(False)
