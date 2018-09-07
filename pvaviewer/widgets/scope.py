#!/usr/bin/env python

import sys
from collections import OrderedDict

import numpy as np
import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
from PyQt5 import QtCore, QtGui


from ..config import Configure
from .uimanage import UiManage
from .liveplot import LivePlot
from ..data import PVAChannelBuffer

class Scope:
    # DEFAULT_N_CHANNELS = 4
    # DEFAULT_N_BINS = 100
    # DEFAULT_REFRESH_RATE_MS = 100  # ms
    # DEFAULT_WINDOW_WIDTH_PX = 640
    # DEFAULT_WINDOW_HEIGHT_PX = 480
    # # DEFAULT_COLORS = ['y', 'm', 'g', 'c', 'b', 'r']
    # DEFAULT_COLORS = ['#FFFF00', '#FF00FF', '#55FF55', '#00FFFF', '#5555FF', '#FF5555']
    #
    # DEFAULT_SELECT_FIELD_GROUP_SIZE = 10

    statistics = {
        'arrays': np.array([]),
        'bytes': np.array([]),
        'lastArrays': 0
    }

    def __init__(self,
                 fieldNameChoices=OrderedDict(),
                 arrayFieldDict=None,
                 **kwargs):
        """
        Initial DaqScope class.

        :param channelName: EPICS 7 channel name
        :param fieldNameChoices: names of interested field in pvChannelName
        :param title: application title
        :param trigger: trigger for scope
        :param trigproto: protocol for trigger PV, 'ca' or 'pva'
        :param samples: default sample numbers
        """
        # parameters from configuration file
        self.defaultCfg = kwargs.get('cfg', None)
        # parameters from command line
        self.cliCfg = kwargs.get('opt', None)

        self.params = {}

        if self.cliCfg.pv:
            self.params["PV"] = self.cliCfg.pv
        else:
            self.params["PV"] = self.defaultCfg['DEFAULT'].get('PV', None)
        if self.params["PV"] is None:
            raise ValueError("EPICS PV name has to be given.")
        else:
            self.params["PV"] = self.params["PV"].strip()

        # get title from configuration
        self.params['TITLE'] = self.defaultCfg['DEFAULT'].get('TITLE', 'DAQ Scope').strip()

        # get trigger name from command line
        # if did not find, get the name from configuration file
        # an empty name means does not use a trigger PV
        trigger = {}
        if self.cliCfg.trigger:
            trigger["PV"] = self.cliCfg.trigger
        elif "TRIGGER" in self.defaultCfg.keys():
            trigpvtmp = self.defaultCfg['TRIGGER'].get("TRIG_PV", None)
            if trigpvtmp is not None and trigpvtmp.strip() != "":
                trigger["PV"] = trigger["PV"].strip()

            # Process trigger pv properties
            # trigger protocol
            trigger_flag = "TRIGGER" in self.defaultCfg.keys()
            if self.cliCfg.trigproto:
                trigger["TRIG_PROTO"] = self.cliCfg.trigproto
            elif trigger_flag:
                trigger["TRIG_PROTO"] = self.defaultCfg['TRIGGER'].get("PROTO", None)
            if trigger["TRIG_PROTO"] is None or trigger["TRIG_PROTO"].lower() not in ['ca', 'pva', 'loc']:
                raise ValueError('Protocol for trigger PV ({}) is not valid'.format(trigger["TRIG_PROTO"]))
            # Ignore trigger for seconds
            if self.cliCfg.trighold:
                trigger['TRIG_HOLDOFF'] = float(self.cliCfg.trighold)
            elif trigger_flag:
                trigger['TRIG_HOLDOFF'] = self.defaultCfg['TRIGGER'].getfloat("HOLDOFF", 0.0)
            # Pause for seconds after trigger is done
            if self.cliCfg.postpause:
                trigger['TRIG_POSTPAUSE'] = float(self.cliCfg.postpause)
            elif trigger_flag:
                trigger['TRIG_POSTPAUSE'] = self.defaultCfg['TRIGGER'].getfloat("POSTPAUSE", 0.0)

            # get more option from configuration
            # TODO add support from command line. Currently available only in configuration file
            if trigger_flag:
                trigger['TRIG_SAMPLE_BEFORE'] = self.defaultCfg['TRIGGER'].getfloat("SAMPLE_BEFORE", 0.0)
                trigger['TRIG_SAMPLE_AFTER'] = self.defaultCfg['TRIGGER'].getfloat("SAMPLE_AFTER", 0.0)
        # finish trigger section
        # trigger is specified
        self.params["TRIGGER"] = trigger

        # Get time field name, default 'time'.
        # Overwrite value from configuration file if user specifies from command line
        if self.cliCfg.timefield:
            self.params['TIME_FIELD'] = self.cliCfg.timefield.strip()
        else:
            self.params['TIME_FIELD'] = self.defaultCfg['DEFAULT'].get('TIMEFIELD', 'time')

        if self.cliCfg.periodfield:
            self.params['PERIOD_FIELD'] = self.cliCfg.periodfield.strip()
        else:
            self.params['PERIOD_FIELD'] = self.defaultCfg['DEFAULT'].get('PERIOD_FIELD', None)

        # Get time field name, default 'time'.
        # Overwrite value from configuration file if user specifies from command line
        if self.cliCfg.freqfield:
            self.params['FREQ_FIELD'] = self.cliCfg.freqfield.strip()
        else:
            self.params['FREQ_FIELD'] = self.defaultCfg['DEFAULT'].get('FREQFIELD', None)

        if self.cliCfg.max:
            self.params['MAX'] = self.cliCfg.max
        else:
            self.params['MAX'] = self.defaultCfg['DEFAULT'].getfloat('MAX', None)
        if self.cliCfg.min:
            self.params['MIN'] = self.cliCfg.min
        else:
            self.params['MIN'] = self.defaultCfg['DEFAULT'].getfloat('MIN', None)

                # Get default sample points
        if self.cliCfg.samples:
            try:
                self.params['N_SAMPLES'] = int(self.cliCfg.samples)
            except ValueError:
                raise ValueError("Number of samples ({}) is not an integer".format(self.cliCfg.samples))
        else:
            self.params['N_SAMPLES'] = self.defaultCfg['DEFAULT'].getint('SAMPLE', 256)

        if self.cliCfg.field:
            self.params["FIELD"] = self.cliCfg.field
        else:
            # by default, get everything
            self.params["FIELD"] = ["None"]

        # default channels to display
        tmp_noc = 4
        if self.cliCfg.noc:
            try:
                tmp_noc = int(self.cliCfg.noc)
            except ValueError:
                raise ValueError("Number to display channel ({}) is not an integer".format(self.cliCfg.noc))
        else:
            tmp_noc = self.defaultCfg['DEFAULT'].getint('N_CHANNELS', 4)
        if tmp_noc < len(self.params["FIELD"]):
            self.params['N_CHANNELS'] = len(self.params["FIELD"])
        else:
            self.params["N_CHANNELS"] = tmp_noc

        # default algorithm to display
        if self.cliCfg.noc:
            self.params['ALGORITHM'] = self.cliCfg.algorithm
        else:
            self.params['ALGORITHM'] = self.defaultCfg['DEFAULT'].get('ALGORITHM', "NORMAL")

        if self.cliCfg.histogram or self.defaultCfg['DEFAULT'].getint('HISTOGRAM') == '1':
            self.params['HISTOGRAM'] = True
        else:
            self.params['HISTOGRAM'] = False

        if self.cliCfg.bins:
            self.params['N_BINS'] = int(self.cliCfg.bins)
        else:
            self.params['N_BINS'] = self.defaultCfg['DEFAULT'].getint('N_BINS', 100)

        if self.cliCfg.rate:
            self.params['REFRESH_RATE'] = float(self.cliCfg.rate)
        else:
            self.params['REFRESH_RATE'] = self.defaultCfg['DEFAULT'].getint('REFRESH_RATE', 100)

        if self.cliCfg.width:
            self.params['WINDOW_WIDTH'] = int(self.cliCfg.width)
        else:
            self.params['WINDOW_WIDTH'] = self.defaultCfg['DEFAULT'].getint('WINDOW_WIDTH', 640)
        if self.cliCfg.height:
            self.params['WINDOW_HEIGHT'] = int(self.cliCfg.height)
        else:
            self.params['WINDOW_HEIGHT'] = self.defaultCfg['DEFAULT'].getint('WINDOW_HEIGHT', 480)

        color = self.defaultCfg['DEFAULT'].get('COLOR', None)
        defaultcolor = ['#FFFF00', '#FF00FF', '#55FF55',
                        '#00FFFF', '#5555FF', '#FF5555']
        if color is not None and color.strip() != "":
             tmpcolor = color.split(',')
             if len(tmpcolor) < len(defaultcolor):
                 self.params['COLOR'] = tmpcolor + defaultcolor[len(tmpcolor):]
             else:
                self.params['COLOR'] = tmpcolor
        else:
            # TODO make the length of color schema same length to avoid any confusion
            self.params['COLOR'] = defaultcolor
        self.params['FIELD_GROUP_SIZE'] = self.defaultCfg['DEFAULT'].getint('FIELD_GROUP_SIZE', 10)

        self.params['IS_FREEZE'] = False
        self.params['IS_WAITTRIG'] = False

        # TODO better way to handle the following 2 options
        self.params['FIELD_NAMES'] = fieldNameChoices
        self.params['ARRAY_FIELD'] = arrayFieldDict
        # self.fieldNameChoices = fieldNameChoices
        # self.arrayFieldDict = arrayFieldDict

    def uilayout(self, uimanage):
        """

        :return:
        """
        self.app = QtGui.QApplication([])
        self.win = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        self.win.setLayout(self.layout)

        self.graph = pg.GraphicsWindow(title=self.params["TITLE"])
        self.layout.addWidget(self.graph, 0, 0, 1, 4)

        self.parameters.sigTreeStateChanged.connect(uimanage.paramChange)
        self.settings = ParameterTree(showHeader=True)
        self.settings.setParameters(self.parameters, showTop=False)
        self.settings.setWindowTitle("Settings")
        self.settings.resize(self.params["WINDOW_WIDTH"], self.params["WINDOW_HEIGHT"])
        self.layout.addWidget(self.settings, 0, 4, 1, 1)
        self.layout.setColumnMinimumWidth(4, self.params["WINDOW_HEIGHT"] / 2)

        self.win.resize(self.params["WINDOW_WIDTH"] * 1.5, self.params["WINDOW_HEIGHT"])
        appName = sys.argv[0].split("/")[-1]
        self.win.setWindowTitle(appName)
        self.win.show()

        # Update the lost PV Array counter every second
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(uimanage.updateUI)
        self.timer.start(1000)

    def setWindowTitle(self, title):
        self.win.setWindowTitle(title)

    def run(self):
        """

        :return:
        """
        trigpvname = None
        try:
            trigpvname = self.params["TRIGGER"]["PV"]
        except KeyError:
            pass
        self.pvaChannel = PVAChannelBuffer(self.params["PV"],
                                           maxlen=self.params["N_SAMPLES"],
                                           pvtrigger_name=trigpvname)
        # set a reference to the prog args so pvaChannel can use them
        self.pvaChannel.setArguments(self.params)

        self.appCfg = Configure(self.params)
        paramcfg = self.appCfg.configureApp()

        self.parameters = Parameter.create(name="params", type="group", children=paramcfg)
        plots = []
        uimanager = UiManage(self.pvaChannel, self.parameters, self.params, plots=plots)
        self.uilayout(uimanager)

        # win, pvaChannel, args, title=None, row=0, col=0, app=None
        liveplot = LivePlot(self.graph,
                            self.pvaChannel,
                            self.params,
                            title=self.params["TITLE"],
                            row=0,
                            col=0,
                            app=self.app,
                            plots=plots
                            )
        liveplot.addPlot(row=0, col=0, title=None)

        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()
            # After app exit, attempt to do some cleanup
            self.pvaChannel.disconnect()
