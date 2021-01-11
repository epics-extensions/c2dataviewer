# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""
from c2dataviewer.view.image_display import ImagePlotWidget
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

        # GUI styles
        self._inputTypeDefaultStyle = self._win.tbValidInput.styleSheet()

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
        self._win.freeze.stateChanged.connect(lambda: self._callback_freeze_changed())

        # # Limit control to avoid overflow network for best performance
        text = self._win.imageWidget._pref["DPXLimit"] or ''
        self._dlg.deadPxLimit.setText(str(text))

        text = self._win.imageWidget._pref["CPULimit"] or ''
        self._dlg.cpuLimit.setText(str(text))

        text = self._win.imageWidget._pref["NetLimit"] or ''
        self._dlg.netLimit.setText(str(text))

        # Min/max channel select
        self.colorChannels = {
            0 : "Red",
            1 : "Green",
            2 : "Blue",
        }
        self.maxChannel = self.colorChannels[0]
        self.minChannel = self.colorChannels[0]
        self._win.maxPixelChannel.addItems(list(self.colorChannels.values()))
        self._win.minPixelChannel.addItems(list(self.colorChannels.values()))
        self._win.maxPixelChannel.setToolTip("Selection for which color channel the value is displayed.")
        self._win.minPixelChannel.setToolTip("Selection for which color channel the value is displayed.")

        # Add tooltips for statistics
        self._win.tbValidInput.setToolTip("Image data type.")
        self._win.runtime.setToolTip("Total time data viewer has been running.")
        self._win.maxPixel.setToolTip("Maximum value in the image. In color modes RGB values are shown. \nIf ROI is selected, value in the \nparentheses apply for the displayed area.")
        self._win.minPixel.setToolTip("Minimum value in the image. In color modes RGB values are shown. \nIf ROI is selected, value in the \nparentheses apply for the displayed area.")
        self._win.frameRateCurrAvg.setToolTip("Current / average Frames Per Second.")
        self._win.nFrames.setToolTip("Total number of frames displayed.")
        self._win.nMissedFramesCurrAvg.setToolTip("Current / average missed frames per second.")
        self._win.nMissedFrames.setToolTip("Total number of missed frames.")
        self._win.deadPixel.setToolTip("Number of pixels that exceed \nthe dead pixel threshold. \nIf ROI is selected, value in the \nparentheses apply for the displayed area.")
        self._win.cpuUsage.setToolTip("CPU usage of the data viewer.")
        self._win.netLoad.setToolTip("Network usage of data viewer.")
        self._win.netReceived.setToolTip("Total number of mega bytes received")


        # Adjust limits panel
        self._win.adjustLimits.clicked.connect(lambda: self.adjustLimits())
        self._dlg.okButton.clicked.connect(lambda: self.acceptNewLimits())
        self._dlg.cancelButton.clicked.connect(lambda: self.cancelNewLimits())

        # Reset statistics
        self._win.resetStatistics.clicked.connect(lambda: self.reset_statistics())

        self._warning.warningConfirmButton.clicked.connect(lambda: self.acceptWarning())


        # Statistics variables
        self.reset_statistics()

        # Statistics update timer. Statistics should be updated once per second.
        self.statistics_timer = kargs.get("timer", None)
        if self.statistics_timer is None:
            raise RuntimeError("No valid timer")
        self.statistics_timer.timeout.connect(self.calculate_statistics)
        self.statistics_timer.start(1000)

        self.frameRateChanged()


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
        fr = list(self._framerates.keys())[n]
        try:
            self._win.imageWidget.set_framerate(self._framerates[fr])
        except NameError:
            pass

    def _callback_freeze_changed(self):
        """
        Called when used freeze or unfreeze the image.

        :return:
        """
        self._win.imageWidget.set_freeze(self._win.freeze.isChecked())

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
        self.reset_statistics()
        try:
            self._win.imageWidget.camera_changed(self._cameras[n])
        except (ValueError, RuntimeError):
            if self._warning is not None:
                self._warning.warningTextBrowse.setText("No data from: {}. Stop image display. \n"
                                                        "Please select a different channel.".
                                                        format(self._cameras[n]))
                self._warning.show()

    def statistics_update(self, valuefield, value, roi_value=None, **kargs):
        """
        Update widget with a new value on the GUI. If limits are specified and value is outside them, text on the widget
        will become red.

        :param valuefield: (QWidget) Widget where status should be written. It must support "setText" and  "setStyleSheet" methods.
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

        if roi_value is not None:
            fmt = f"{fmt} ({fmt})"
            if type(value) is tuple:
                value = value + roi_value
            else:
                value = (value, roi_value)

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


    def calculate_statistics(self):
        """
        Calculate statistics.

        :return:
        """

        # Get current time
        now = ptime.time()

        # Set required variabels on first call
        if self._last_time_stat_calculated is None:
            self._last_time_stat_calculated = now
            return

        # Calculate runtime
        self.runtime = now - self._start_time

        # Calculate time difference betwean calls
        delta_time = now - self._last_time_stat_calculated
        self._delta_time.append(delta_time)
        self._delta_time = self._delta_time[-3:]

        # Calculate number of frames displayed betwean calls
        delta_frames = self._win.imageWidget.frames_displayed - self._last_frames
        self._last_frames = self._win.imageWidget.frames_displayed
        self._delta_frames.append(delta_frames)
        self._delta_frames = self._delta_frames[-3:]
        try:
            self.fps_current = sum(self._delta_frames) / sum(self._delta_time)
        except:
            self.fps_current = 0
        self.fps_current = self.fps_current if self.fps_current >=0 else 0
        self.fps_average = self._win.imageWidget.frames_displayed / self.runtime

        # Calculate number of missed frames betwean calls
        delta_missed_frames = self._win.imageWidget.frames_missed - self._last_missed_frames
        self._last_missed_frames = self._win.imageWidget.frames_missed
        self._delta_missed_frames.append(delta_missed_frames)
        self._delta_missed_frames = self._delta_missed_frames[-3:]
        try:
            self.frames_missed_current = sum(self._delta_missed_frames) / sum(self._delta_time)
        except:
            self.frames_missed_current = 0
        self.frames_missed_current = self.frames_missed_current if self.frames_missed_current >=0 else 0
        self.frames_missed_average = self._win.imageWidget.frames_missed / self.runtime

        # Calculate number of bytes received betwean calls
        delta_bytes = self._win.imageWidget.MB_received - self._last_MB_received
        self._last_MB_received = self._win.imageWidget.MB_received
        self._delta_bytes.append(delta_bytes)
        self._delta_bytes = self._delta_bytes[-3:]

        # Calculate machine resources usage
        with self._win._proc.oneshot():
            self.cpu_usage = self._win._proc.cpu_percent(None)
        try:
            self.network_usage = sum(self._delta_bytes) / sum(self._delta_time)
        except:
            self.network_usage = 0
        if self.network_usage < 0:
            self.network_usage = 0

        # Update time when statistics were updated
        self._last_time_stat_calculated = now

        # Update the GUI
        self.updateStatus()

    def reset_statistics(self):
        """
        Reset all the statistics.

        :return:
        """
        self._last_time_stat_calculated = None
        self._win.imageWidget.__last_array_id = None
        self._start_time = ptime.time()
        self.runtime = 0
        self._win.imageWidget.MB_received = 0.0
        self._win.imageWidget.frames_displayed = 0
        self._last_frames = 0
        self.fps_current = 0
        self.fps_average = 0
        self._win.imageWidget.frames_missed = 0
        self._last_missed_frames = 0
        self.frames_missed_current = 0
        self.frames_missed_average = 0
        self._last_MB_received = 0
        self.cpu_usage = 0
        self.network_usage = 0
        self._delta_frames = [0]
        self._delta_missed_frames = [0]
        self._delta_bytes = [0]
        self._delta_time = [1]


    def updateStatus(self):
        """
        Update all the statistics values on the GUI.

        :return:
        """
        # Update input type
        self._win.tbValidInput.setText(self._win.imageWidget._inputType + " / "
                                      + self._win.imageWidget.COLOR_MODES.get(self._win.imageWidget.color_mode, "Unknown")
                                      + ("" if self._win.imageWidget._isInputValid else " (Invalid)"))
        if self._win.imageWidget._isInputValid:
            self._win.tbValidInput.setStyleSheet(self._inputTypeDefaultStyle)
        else:
            self._win.tbValidInput.setStyleSheet('background-color : red;')

        # Update runtime
        self._win.runtime.setText(str(datetime.timedelta(seconds=round(self.runtime))))

        # Max / min pixels
        isZoomedImage = self._win.imageWidget.is_zoomed()
        xOffset, yOffset, width, height = self._win.imageWidget.get_zoom_region()
        if self._win.imageWidget.color_mode == ImagePlotWidget.COLOR_MODE_MONO:
            self._win.maxPixelChannel.hide()
            self._win.minPixelChannel.hide()
            max_val = self._win.imageWidget._max
            min_val = self._win.imageWidget._min
            max_val_roi = self._win.imageWidget._maxRoi if isZoomedImage else None
            min_val_roi = self._win.imageWidget._minRoi if isZoomedImage else None
        else:
            self._win.maxPixelChannel.show()
            self._win.minPixelChannel.show()
            max_val = self._win.imageWidget._max[self._win.maxPixelChannel.currentIndex()]
            min_val = self._win.imageWidget._min[self._win.minPixelChannel.currentIndex()]
            max_val_roi = self._win.imageWidget._maxRoi[self._win.maxPixelChannel.currentIndex()] if isZoomedImage else None
            min_val_roi = self._win.imageWidget._minRoi[self._win.minPixelChannel.currentIndex()] if isZoomedImage else None

        self.statistics_update(self._win.maxPixel, max_val, max_val_roi)
        self.statistics_update(self._win.minPixel, min_val, min_val_roi)

        # Update frames information
        self.statistics_update(self._win.frameRateCurrAvg,
                        (self.fps_current, self.fps_average),
                        fmt='%.0f / %.2f',
                        lolimit=self._win.imageWidget._pref['FPSLimit'])
        self.statistics_update(self._win.nFrames, self._win.imageWidget.frames_displayed, fmt='%d')
        self.statistics_update(self._win.nMissedFramesCurrAvg,
                            (self.frames_missed_current, self.frames_missed_average),
                            fmt = '%.0f / %.2f')
        self.statistics_update(self._win.nMissedFrames, self._win.imageWidget.frames_missed, fmt='%d')

        # No. of dead pixels
        if isZoomedImage:
            values = (max(self._win.imageWidget._dpx), max(self._win.imageWidget._dpxRoi))
            fmt = '%.0f (%.0f)'
        else:
            values = (max(self._win.imageWidget._dpx))
            fmt = '%.0f'
        self.statistics_update(self._win.deadPixel,
                                values,
                                fmt=fmt,
                                hilimit=self._win.imageWidget._pref["DPXLimit"])

        # Machine resources
        self.statistics_update(self._win.cpuUsage,
                                self.cpu_usage,
                                hilimit=self._win.imageWidget._pref['CPULimit'],
                                callback=True)
        self.statistics_update(self._win.netLoad,
                                self.network_usage,
                                fmt='%.2f',
                                hilimit=self._win.imageWidget._pref['NetLimit'],
                                callback=True)
        self.statistics_update(self._win.netReceived,
                                self._win.imageWidget.MB_received,
                                fmt='%.2f')


        # Update image and zoom section
        self._win.lblXsize.setText(' '.join([str(self._win.imageWidget.x),
                '' if not isZoomedImage else f"({xOffset}-{xOffset+width})"
                                            ]))
        self._win.lblYsize.setText(' '.join([str(self._win.imageWidget.y),
                '' if not isZoomedImage else f"({yOffset}-{yOffset+height})"
                                            ]))
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

        # General update TODO: why is this required?
        self._win.setStyleSheet('color: black; font-weight: normal')


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
