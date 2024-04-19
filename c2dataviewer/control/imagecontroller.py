# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""
import datetime
from pyqtgraph import Qt
from pyqtgraph import QtCore
import time
from pyqtgraph.functions import mkPen
from pyqtgraph import PlotWidget
from PyQt5 import QtWidgets

from ..view.image_definitions import COLOR_MODE_MONO, COLOR_MODES
from ..model import ConnectionState

class ImageController:

    SLIDER_MAX_VAL = 1_000_000_000
    SLIDER_MIN_VAL = -SLIDER_MAX_VAL
    SPINNER_MAX_VAL = 1.7976931348623157e+308
    SPINNER_MIN_VAL = -SPINNER_MAX_VAL

    HIDE_CONTROL_TEXT = 'Hide Control Panel'
    SHOW_CONTROL_TEXT = 'Show Control Panel'
    HIDE_XY_INTENSITY_TEXT = 'Hide Coordinates and Intensity'
    SHOW_XY_INTENSITY_TEXT = 'Show Coordinates and Intensity'
    RESET_ZOOM_TEXT = 'Reset Zoom'
    ENABLE_ROI_MODE_TEXT = 'Enable ROI Mode'
    DISABLE_ROI_MODE_TEXT = 'Disable ROI Mode'

    def __init__(self, widget, **kargs):
        """

        :param widget:
        :param kargs:
        """
        self._win = widget
        if self._win is None:
            raise RuntimeError("Widget is unknown")

        cameras = kargs.get("PV", None)

        self.profilesWidgetMutex = QtCore.QMutex()
        self.profilesWidgetDisplayed = False

        self.datareceiver = kargs.get('data', None)

        self._win.pvPrefix.setEditable(True)
        self._win.pvPrefix.setInsertPolicy(Qt.QtWidgets.QComboBox.InsertAtBottom)
        if cameras is not None:
            self._win.pvPrefix.addItems(cameras)
        self._win.pvPrefix.currentIndexChanged.connect(self.camera_changed)
        self._win.imageWidget.connection_changed_signal.connect(self.connection_changed)
        
        self._image_settings_dialog  = kargs.get("IMAGE_SETTINGS_DIALOG", None)
        self._warning = kargs.get("WARNING", None)

        # GUI styles
        self._inputTypeDefaultStyle = self._win.tbValidInput.styleSheet()

        # Image and zoom
        self._win.lblXsize.setToolTip("Number of pixels image has in X direction. \nIf ROI is selected, numbers in parentheses \nshow the size and range of displayed pixels.")
        self._win.lblYsize.setToolTip("Number of pixels image has in Y direction. \nIf ROI is selected, numbers in parentheses \nshow the size and range of displayed pixels.")
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
        self._image_settings_dialog.blackMin.setMinimum(self.SPINNER_MIN_VAL)
        self._image_settings_dialog.blackMin.setMaximum(self.SPINNER_MAX_VAL)
        self._image_settings_dialog.blackMax.setMinimum(self.SPINNER_MIN_VAL)
        self._image_settings_dialog.blackMax.setMaximum(self.SPINNER_MAX_VAL)
        self._image_settings_dialog.whiteMin.setMinimum(self.SPINNER_MIN_VAL)
        self._image_settings_dialog.whiteMin.setMaximum(self.SPINNER_MAX_VAL)
        self._image_settings_dialog.whiteMax.setMinimum(self.SPINNER_MIN_VAL)
        self._image_settings_dialog.whiteMax.setMaximum(self.SPINNER_MAX_VAL)
        self._image_settings_dialog.displayQueueSize.setMinimum(self._win.imageWidget.MIN_DISPLAY_QUEUE_SIZE)
        self._image_settings_dialog.displayQueueSize.setMaximum(self._win.imageWidget.MAX_DISPLAY_QUEUE_SIZE)
        self._image_settings_dialog.sbCpuLimit.setMinimum(10)
        self._image_settings_dialog.sbCpuLimit.setMaximum(400)
        self._image_settings_dialog.sbNetworkLimit.setMinimum(10)
        self._image_settings_dialog.sbNetworkLimit.setMaximum(1250) # 1250 megabyte = 10 gigabit
        self._image_settings_dialog.sbServerQueueSize.setMinimum(0)
        self._image_settings_dialog.sbServerQueueSize.setMaximum(10000)

        # Configure settings window tooltips
        self._image_settings_dialog.sbDeadPixelThreshold.setToolTip("Dead pixel threshold. \nPixel values above this setting are counted as 'dead'.")
        self._image_settings_dialog.sbEmbeddedDataLength.setToolTip("Number of pixels at the beggining of the image that hold the embedded data. \nThese pixels are not included in the statistics calculations.")
        self._image_settings_dialog.sbCpuLimit.setToolTip("Maximum allowed usage of the CPU. \n100% = 1 full CPU core.")
        self._image_settings_dialog.sbNetworkLimit.setToolTip("Maximum allowed usage of the network in MB/s.")
        self._image_settings_dialog.sbServerQueueSize.setToolTip("Maximum number of frames to be queued on the server side.")

        # Settings dialog callbacks
        self._win.btnSettings.clicked.connect(lambda: self._callback_adjust_image_settings())
        self._image_settings_dialog.okButton.clicked.connect(lambda: self._callback_accept_new_image_settings())
        self._image_settings_dialog.cancelButton.clicked.connect(lambda: self._callback_cancel_new_image_settings())

        # Frame DAQ control
        self._framerates = {'1 Hz': 1, '2 Hz': 2, '5 Hz': 5, '10 Hz': 10, '20 Hz': 20, '30 Hz': 30, 'Full IOC Rate': -1} #Full IOC rate must be on the last place
        self._win.iocRate.addItems(self._framerates.keys())
        self._win.iocRate.setCurrentIndex(2)
        self.frameRateChanged()
        self._win.iocRate.currentIndexChanged.connect(lambda: self.frameRateChanged())
        self._win.freeze.stateChanged.connect(lambda: self._callback_freeze_changed())


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
        self._win.frameRateCurrAvg.setToolTip("Current / average display Frames Per Second.")
        self._win.receiveRateCurrAvg.setToolTip("Current / average receive Frames Per Second.")
        self._win.nFrames.setToolTip("Total number of frames processed/displayed. \nSome frames can be skipped for drawing if the painter can not keep up.")
        self._win.nMissedFramesCurrAvg.setToolTip("Current / average missed frames per second.")
        self._win.nMissedFrames.setToolTip("Total number of missed frames.")
        self._win.deadPixel.setToolTip("Number of pixels that exceed \nthe dead pixel threshold. \nIf ROI is selected, value in the \nparentheses apply for the displayed area. \nThis can be configured under 'Settings'.")
        self._win.cpuUsage.setToolTip("CPU usage of the data viewer.")
        self._win.netLoad.setToolTip("Network usage of data viewer.")
        self._win.netReceived.setToolTip("Total number of mega bytes received")

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

        # Setup profiles
        self._win.imageWidget.setup_profiles(self._win.canvasGrid)
        #self._win.cbShowProfiles.stateChanged.connect(
        #    lambda: self._callback_profiles_show_changed(self._win.cbShowProfiles))
        self._win.cbShowProfiles.stateChanged.connect(self._callback_profiles_show_changed)
        self._win.cbShowRulers.stateChanged.connect(self._callback_profiles_show_changed)

        self.frameRateChanged()
        self.camera_changed()

        self._imageContextMenu = QtWidgets.QMenu(self._win.imageWidget)
        self._imageContextMenuAction = QtWidgets.QAction(self.HIDE_CONTROL_TEXT, self._win.imageWidget)
        self._imageContextMenu.addAction(self._imageContextMenuAction)

        self._imageXY_IntensityDialogAction = QtWidgets.QAction(self.SHOW_XY_INTENSITY_TEXT, self._win.imageWidget)
        self._imageContextMenu.addAction(self._imageXY_IntensityDialogAction)
        self._imageResetZoomAction = QtWidgets.QAction(self.RESET_ZOOM_TEXT, self._win.imageWidget)
        self._imageContextMenu.addAction(self._imageResetZoomAction)
        self._imageRoiModeAction = QtWidgets.QAction(self.ENABLE_ROI_MODE_TEXT, self._win.imageWidget)
        self._imageContextMenu.addAction(self._imageRoiModeAction)
        
        self._win.imageWidget.right_button_clicked_signal.connect(lambda point: self.on_context_menu(point))

        self._scrollAreaWidth = 0

    def on_context_menu(self, point):
        # show context menu
        action = self._imageContextMenu.exec_(self._win.imageWidget.mapToGlobal(point))
        if not action:
            return
        if action.text() == self.HIDE_CONTROL_TEXT:
            action.setText(self.SHOW_CONTROL_TEXT)
            self._win.scrollArea.setHidden(True)
            self._scrollAreaWidth = self._win.scrollArea.parent().minimumWidth()
            self._win.scrollArea.parent().setMinimumWidth(0)
            self._win.scrollArea.parent().setMinimumHeight(0)
        elif action.text() == self.SHOW_CONTROL_TEXT:
            action.setText(self.HIDE_CONTROL_TEXT)
            self._win.scrollArea.setHidden(False)
            self._win.scrollArea.parent().setMinimumWidth(self._scrollAreaWidth)
        elif action.text() == self.SHOW_XY_INTENSITY_TEXT:
            action.setText(self.HIDE_XY_INTENSITY_TEXT)
            self._win.imageWidget.mouse_dialog.enable_mouse_dialog()
            self._win.imageWidget.setMouseTracking(True)
        elif action.text() == self.HIDE_XY_INTENSITY_TEXT:
            action.setText(self.SHOW_XY_INTENSITY_TEXT)
            self._win.imageWidget.mouse_dialog.disable_mouse_dialog()
            self._win.imageWidget.setMouseTracking(False)
        elif action.text() == self.RESET_ZOOM_TEXT:
            self._win.imageWidget.reset_zoom()
        elif action.text() == self.ENABLE_ROI_MODE_TEXT:
            action.setText(self.DISABLE_ROI_MODE_TEXT)
            self._win.imageWidget.createZoomSelectionIndicator(roi_mode=True)
        elif action.text() == self.DISABLE_ROI_MODE_TEXT:
            action.setText(self.ENABLE_ROI_MODE_TEXT)
            self._win.imageWidget.createZoomSelectionIndicator(roi_mode=False)
        self._win.imageWidget.adjustSize()

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

    def _callback_profiles_show_changed(self):
        """
        Callback used when the user on the GUI ticks or un-ticks the "Show
        the image profiles" or the "Show image rulers" bottons.

        :return:
        """
        self.profilesWidgetMutex.lock()
        try:
            profilesWidgetDisplayed = self._win.cbShowProfiles.isChecked() or self._win.cbShowRulers.isChecked()
            self._win.imageWidget.image_profile_widget.showProfiles(self._win.cbShowProfiles.isChecked())
            self._win.imageWidget.image_profile_widget.showRulers(self._win.cbShowRulers.isChecked())
            self._win.imageWidget.rulersDisplayed(self._win.cbShowRulers.isChecked())
            if profilesWidgetDisplayed == self.profilesWidgetDisplayed:
                # If widget is shown already, we are done here
                return
            self.profilesWidgetDisplayed = profilesWidgetDisplayed
            if profilesWidgetDisplayed:
                self._win.iocRate.blockSignals(True)
                self._win.iocRate.removeItem(len(self._framerates)-1)
                self._win.iocRate.blockSignals(False)
                new_freq_key = list(self._framerates.keys())[list(self._framerates.values()).index(1)] # Get key for 1 Hz
                self._win.iocRate.setCurrentText(new_freq_key)
                self._win.imageWidget.image_profile_widget.show(True)
            else:
                self._win.imageWidget.image_profile_widget.show(False)
                full_rate_key = list(self._framerates.keys())[-1]
                self._win.iocRate.addItem(full_rate_key, self._framerates[full_rate_key])

            if self._win.freeze.isChecked() and cb.isChecked():
                self._win.imageWidget.calculate_profiles(self._win.imageWidget.last_displayed_image)
                self._win.imageWidget._set_image_signal.emit()
        finally:
            self.profilesWidgetMutex.unlock()

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


    def _callback_adjust_image_settings(self):
        """
        This callback is called when user press the "Settings" button.
        It will open the pop screen which allow to change different types of settings.

        :return:
        """
        # Set current values
        self._image_settings_dialog.blackMin.setValue(self._win.imageBlackSpinBox.minimum())
        self._image_settings_dialog.blackMax.setValue(self._win.imageBlackSpinBox.maximum())
        self._image_settings_dialog.whiteMin.setValue(self._win.imageWhiteSpinBox.minimum())
        self._image_settings_dialog.whiteMax.setValue(self._win.imageWhiteSpinBox.maximum())
        self._image_settings_dialog.whiteMax.setValue(self._win.imageWhiteSpinBox.maximum())

        self._image_settings_dialog.displayQueueSize.setValue(self._win.imageWidget.get_display_max_queue_size())

        self._image_settings_dialog.cbEnableDeadPixels.setChecked(self._win.imageWidget.get_preferences()['DPXEnabled'])
        self._image_settings_dialog.sbDeadPixelThreshold.setValue(self._win.imageWidget.get_preferences()['DPXLimit'])
        self._image_settings_dialog.sbEmbeddedDataLength.setValue(self._win.imageWidget.get_preferences()['EmbeddedDataLen'])

        self._image_settings_dialog.cbEnableCpuLimit.setChecked(self._win.imageWidget.get_preferences()['EnableCPULimit'])
        self._image_settings_dialog.sbCpuLimit.setValue(self._win.imageWidget.get_preferences()['CPULimit'])
        self._image_settings_dialog.cbEnableNetworkLimit.setChecked(self._win.imageWidget.get_preferences()['EnableNetLimit'])
        self._image_settings_dialog.sbNetworkLimit.setValue(self._win.imageWidget.get_preferences()['NetLimit'])
        self._image_settings_dialog.cbEnableServerQueue.setChecked(self._win.imageWidget.get_preferences()['EnableServerQueue'])
        self._image_settings_dialog.sbServerQueueSize.setValue(self._win.imageWidget.get_preferences()['ServerQueueSize'])

        # Launch the dialog
        self._image_settings_dialog.exec_()


    def _callback_accept_new_image_settings(self):
        """
        This callback is called when the user confirms the new settings.

        :return:
        """
        self.changeimageBlackLimits(self._image_settings_dialog.blackMin.value(),
                                    self._image_settings_dialog.blackMax.value())
        self.changeimageWhiteLimits(self._image_settings_dialog.whiteMin.value(),
                                   self._image_settings_dialog.whiteMax.value())

        preferences = {
            'DPXEnabled' : self._image_settings_dialog.cbEnableDeadPixels.isChecked(),
            'DPXLimit' : self._image_settings_dialog.sbDeadPixelThreshold.value(),
            'EmbeddedDataLen' : self._image_settings_dialog.sbEmbeddedDataLength.value(),
            'EnableCPULimit' : self._image_settings_dialog.cbEnableCpuLimit.isChecked(),
            'CPULimit' : self._image_settings_dialog.sbCpuLimit.value(),
            'EnableNetLimit' : self._image_settings_dialog.cbEnableNetworkLimit.isChecked(),
            'NetLimit' : self._image_settings_dialog.sbNetworkLimit.value(),
            'EnableServerQueue' : self._image_settings_dialog.cbEnableServerQueue.isChecked(),
            'ServerQueueSize' : self._image_settings_dialog.sbServerQueueSize.value(),
        }
        self._win.imageWidget.set_preferences(preferences)

        self._win.imageWidget.set_display_queue_size(self._image_settings_dialog.displayQueueSize.value())

        # Force start/stop if we modified preferences that affect ioc rates
        self.frameRateChanged()

        self._image_settings_dialog.close()

    def _callback_cancel_new_image_settings(self):
        """
        This callback is called when user cancels the new settings.

        :return:
        """
        self._image_settings_dialog.reject()

    def acceptWarning(self):
        """

        :return:
        """
        self._warning.close()

    def notify_warning(self, msg):
        if self._warning is not None:
            self.acceptWarning()
            self._warning.warningTextBrowse.setText(msg)
            self._warning.show()
        
    def connection_changed(self, status, msg):
        if status == str(ConnectionState.FAILED_TO_CONNECT):
            self.notify_warning('Connection lost: ' + msg)
        
        self._win.lblConnectionStatus.setText(str(status))
        
    def camera_changed(self):
        """

        :param value:
        :return:
        """

        self.reset_statistics()
        pv = self._win.pvPrefix.currentText()
        try:
            self._win.imageWidget.camera_changed(pv)
        except (ValueError, RuntimeError):
            self.notify_warning("No data from: {}. Stop image display. \n"
                                "Please select a different channel.".
                                format(pv))

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

        if type(value) is list:
            value = value[0]
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
        # Handle mouse dialog when freeze enabled
        if self._win.imageWidget._freeze and self._win.imageWidget.mouse_dialog.mouse_dialog_enabled:
            self._win.imageWidget.setup_mouse_textbox()

        # Get current time
        now = time.time()

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
        except: # pylint: disable=bare-except
            self.fps_current = 0
        self.fps_current = self.fps_current if self.fps_current >=0 else 0
        self.fps_average = self._win.imageWidget.frames_displayed / self.runtime

        # Calculate number of frames received betwean calls
        delta_frames_received = self._win.imageWidget.frames_received - self._last_frames_received
        self._last_frames_received = self._win.imageWidget.frames_received
        self._delta_frames_received.append(delta_frames_received)
        self._delta_frames_received = self._delta_frames_received[-3:]
        try:
            self.fps_current_received = sum(self._delta_frames_received) / sum(self._delta_time)
        except: # pylint: disable=bare-except
            self.fps_current_received = 0
        self.fps_current_received = self.fps_current_received if self.fps_current_received >=0 else 0
        self.fps_average_received = self._win.imageWidget.frames_received / self.runtime

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
        self._start_time = time.time()
        self.runtime = 0
        self._win.imageWidget.MB_received = 0.0
        self._win.imageWidget.frames_received = 0
        self._win.imageWidget.frames_displayed = 0
        self._last_frames = 0
        self._last_frames_received = 0
        self.fps_current = 0
        self.fps_current_received = 0
        self.fps_average = 0
        self.fps_average_received = 0
        self._win.imageWidget.frames_missed = 0
        self._last_missed_frames = 0
        self.frames_missed_current = 0
        self.frames_missed_average = 0
        self._last_MB_received = 0
        self.cpu_usage = 0
        self.network_usage = 0
        self._delta_frames = [0]
        self._delta_frames_received = [0]
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
                                      + COLOR_MODES.get(self._win.imageWidget.color_mode, "Unknown")
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
        if self._win.imageWidget.color_mode == COLOR_MODE_MONO:
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
        self.statistics_update(self._win.receiveRateCurrAvg,
                        (self.fps_current_received, self.fps_average_received),
                        fmt='%.0f / %.2f',
                        lolimit=self._win.imageWidget._pref['FPSLimit'])
        self.statistics_update(self._win.nFrames,
                        (self._win.imageWidget.frames_displayed, self._win.imageWidget.frames_received),
                        fmt='%d / %d')
        self.statistics_update(self._win.nMissedFramesCurrAvg,
                            (self.frames_missed_current, self.frames_missed_average),
                            fmt = '%.0f / %.2f')
        self.statistics_update(self._win.nMissedFrames, self._win.imageWidget.frames_missed, fmt='%d')
        self.statistics_update(self._win.nQueueSize,
                            (self._win.imageWidget.get_display_queue_size(), self._win.imageWidget.get_display_max_queue_size()),
                            fmt = '%d / %d')

        # No. of dead pixels
        if isZoomedImage:
            values = (max(self._win.imageWidget.dead_pixels), max(self._win.imageWidget.dead_pixels_roi))
            fmt = '%.0f (%.0f)'
        else:
            values = (max(self._win.imageWidget.dead_pixels))
            fmt = '%.0f'
        self.statistics_update(self._win.deadPixel,
                                values,
                                fmt=fmt,
                                hilimit=self._win.imageWidget._pref["DPXLimit"])

        # Machine resources
        self.statistics_update(self._win.cpuUsage,
                                self.cpu_usage,
                                hilimit=self._win.imageWidget._pref['CPULimit'] if self._win.imageWidget._pref['EnableCPULimit'] else None,
                                callback=self._win.imageWidget._pref['EnableCPULimit'])
        self.statistics_update(self._win.netLoad,
                                self.network_usage,
                                fmt='%.2f',
                                hilimit=self._win.imageWidget._pref['NetLimit'] if self._win.imageWidget._pref['EnableNetLimit'] else None,
                                callback=self._win.imageWidget._pref['EnableNetLimit'])
        self.statistics_update(self._win.netReceived,
                                self._win.imageWidget.MB_received,
                                fmt='%.2f')


        # Update image and zoom section
        self._win.lblXsize.setText(' '.join([str(self._win.imageWidget.x),
                '' if not isZoomedImage else f"({width}|{xOffset}-{xOffset+width})"
                                            ]))
        self._win.lblYsize.setText(' '.join([str(self._win.imageWidget.y),
                '' if not isZoomedImage else f"({height}|{yOffset}-{yOffset+height})"
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

        # Update the values on the settings dialog
        self._image_settings_dialog.currentDisplayQueueSize.setText(str(self._win.imageWidget.draw_queue.qsize()))

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
        self._win.imageBlackSlider.setMinimum(int(minVal * sliderFactor))
        self._win.imageBlackSlider.setMaximum(int(maxVal * sliderFactor))

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
        self._win.imageWhiteSlider.setMinimum(int(minVal * sliderFactor))
        self._win.imageWhiteSlider.setMaximum(int(maxVal * sliderFactor))

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
        self._win.imageBlackSlider.setValue(int(value * self._imageBlackSliderFactor))
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
        self._win.imageWhiteSlider.setValue(int(value * self._imageWhiteSliderFactor))
        self._win.imageWhiteSlider.blockSignals(False)
