# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

"""
import numpy as np

# TODO remove GUI related function from data source
from PyQt5 import QtCore

import pvaccess


class PVAChannelBuffer():
    data = {}

    def __init__(self, name, maxlen=1024, pvtrigger_name=None):
        """

        :param name:
        :param maxlen:
        :param pvtrigger_name:
        """
        self.channel = pvaccess.Channel(name)
        self.channel.subscribe('callback', self.callback)
        self.maxlen = maxlen
        self.mutex = QtCore.QMutex()
        self.lastArrayId = None
        self.lostArrays = 0
        self.size = 0
        self.arraysReceived = 0

        self.channame = name
        # keep a copy of the program arguments locally.
        # we default to None, but calling progarm can set this with setprogargs.
        self.args = None

        #
        # We keep track of sec past epoch time stamp if it is provided. each data block has
        # a timestamp marking the 1st sample in that block. as we append the block to circle buffer
        # we must keep an index as to where inthe buffer the lastest timestamp refers. This allows to
        # calc the timestamp of the 1st sample int he circle buffer.
        #

        # index from beginning of buffer of latest timestamped sample. if latest block has timestamp the stamp
        # 1st sample of that block. the sample is put into the circle buffer at some index.
        # !!self.ts_index_of_last_timestamp = 0
        # copy of latest timestamp from latest block from server
        # !!self.ts_latest_timestamp = 0.0
        # calculated timestamp of the top of the circullar buffer, calculated from latest timestamp, position of last
        # block in the circle buffer
        # !!self.ts_circ_buffer_timestamp = 0.0



        class Foo(QtCore.QObject):

            my_signal = QtCore.pyqtSignal()

            def __init__(self):
                QtCore.QObject.__init__(self)

        self.plot_signal_emitter = Foo()

        # self.plotview = None

        #
        # Trigger mode variables
        #

        # epics v3 pv name
        # self.pvtrigger_name = "None"
        self.pvtrigger_name = pvtrigger_name
        # scope looks for triggers
        self.trigger_mode = False
        # num samples to take after trugger
        self.samples_after_trig = 0
        # number of sample captured after trigger
        self.samples_after_trig_cnt = 0
        # handle to Channel obj
        self.trigger_pv = None
        # true if in trig mode and trig was received. that is the pv mon fired.
        self.is_triggered = False
        # counts whenever trigger pv monitor fires callback
        self.trigger_count = 0
        # true of we are monitoring a channel
        self.trigger_is_monitor = False
        # true if we put in bad pv name, and try to monitir
        self.trigger_pv_error = False
        # double sec past epoch timestamp from the trig pv
        self.trigger_timestamp = 0.0
        #
        # End Trigger mode variables
        #

        # Setup storage buffer
        changet = self.channel.get('')
        newData = changet.toDict().items()
        # store a list of keys or filld names in the pvdata
        self.pvdatakeys = changet.toDict().keys()

        for k, v in newData:
            if type(v) == list:  # should epics v4 lib not have np, we "fix" it by converting list to np
                v = np.array(v)
            if type(v) != np.ndarray: continue
            if len(v) == 0: continue
            self.data[k] = np.array([], dtype=v.dtype)

            # !! TJM no reason to start monitor
            # self.channel.startMonitor('')

    # set a copy of DaqScope.args here so this obj as access to it.
    def setArguments(self, args_):
        self.args = args_

    def startTriggerPVMode(self, trig_pvname, samples_after_trig):
        # epics v3 pv name
        # if we have a new pv, and also monitoring a pv, then we disconnect.
        if self.trigger_is_monitor and trig_pvname != self.pvtrigger_name:
            self.stopTriggerPVMode(True)

        self.trig_is_holdoff_ignore = False
        self.pvtrigger_name = trig_pvname
        self.trigger_mode = True
        self.samples_after_trig = samples_after_trig
        self.samples_after_trig_cnt = 0
        # we could have 64 waveforms in the pv, so we keep copint of all of them
        if len(self.pvtrigger_name) == 0:
            print("Error- no pv name. hit return in gui")
            return

        if not self.trigger_is_monitor:
            try:
                # TODO add support for local simulator
                proto = pvaccess.CA
                if self.args["TRIGGER"]["TRIG_PROTO"] == "PVA":
                    proto = pvaccess.PVA
                self.trigger_pv = pvaccess.Channel(str(self.pvtrigger_name), proto)
                self.trigger_pv.subscribe('callback', self.trigCallback)
                self.trigger_pv.startMonitor('field(value,timeStamp)')
                print("Start trig monitor")
                self.trigger_count = 0
                self.trigger_is_monitor = True
            except:
                self.trigger_is_monitor = False
                print("Error- cannot monitor trig pv: %s" % str(self.pvtrigger_name))
                self.trigger_pv_error = True
        else:
            print('To Trig mode, already connected to PV')

        self.is_triggered = False

    def stopTriggerPVMode(self, is_disconnect=False):
        self.trigger_mode = False
        print("Stop trigger monitor")
        if is_disconnect and self.trigger_pv is not None:
            self.trigger_pv.stopMonitor()
            self.trigger_is_monitor = False
            self.trigger_count = 0

    def trigCallback(self, trigdata):
        self.trigger_count = self.trigger_count + 1
        td = trigdata.toDict()
        ts = td['timeStamp']
        # because the callback happens on connection, we set flag on 2nd callback, when monitor fires for real.
        # also, we only call this stuff if istriggered==False so we dont retrigger before we process the last trigger.
        # also, if holdoff ignore, then diring a hold off time, we ignore triggers. example we ignore trigs for 1sec
        if self.trigger_count > 1 and self.is_triggered == False:
            self.is_triggered = True
            self.samples_after_trig_cnt = 0
            self.trigger_timestamp = ts['secondsPastEpoch'] + 1e-9 * ts['nanoseconds']
            print("Triggered: %d, %s" % (self.trigger_count, td))
            print('TS %20.10f' % (self.trigger_timestamp))

    def setMaxLen(self, maxlen):
        self.maxlen = maxlen

    def isFilling(self, fieldName):
        dataArray = self.data.get(fieldName, [])
        return len(dataArray) < self.maxlen

    def getFieldData(self, fieldName):
        return self.data.get(fieldName)

    def wait(self):
        self.mutex.lock()

    def signal(self):
        self.mutex.unlock()

    def callback(self, data):
        newData = data.toDict().items()
        newSize = self.size
        self.wait()

        # assume a triggers done then set false when we gather data.
        all_triggers_done = True
        # we step through all the signals we get from the v4 pv. we keep a count of them
        signalcount = -1  # start at -1 so we inc to 0 at beginning of loop
        # the first np array is the one we determine trigger position in the data. so as we step all data vectors
        # with k, the 1st vector we mark as "my_trigger_vector"
        my_trigger_vector = -1
        for k, v in newData:
            # if k == 'DspLoopRate':
            #    self.data[k] = v
            if k == 'ArrayId':
                if self.lastArrayId is not None:
                    if v - self.lastArrayId > 1:
                        self.lostArrays += 1
                self.lastArrayId = v
                if self.size == 0:
                    newSize += 4
            # if epics v4 does not have numpy, then we get lists. convert lists to np arrays
            if type(v) == list: v = np.array(v)

            # when program is here, the v4 field is either a np array, or some sort of scaler.
            # if not an array then we have a scalar, so store the scaler into the local copy of data,
            # and do NOT add to a long stored buffer
            if type(v) != np.ndarray:
                self.data[k] = v
            else:
                # at this point in program we found an nd array that may or may not have data. nd array is
                # not a mark rivers NDArray, but a numpy ndarray.
                # if no data in aa pv field, we just skip this whole loop iteration.
                if len(v) == 0:
                    continue

                # if we get here, then we found an epics array in the v4 pv that has data.
                # we cound arrau type signals that have data, so triggering works.
                signalcount += 1
                # the 1st time we get here, we actaully found k pointing to a data vector,
                # so mark the index of the signal
                if my_trigger_vector == -1:
                    my_trigger_vector = signalcount

                vector_len = len(v)

                # self.data[k] = np.append(self.data.get(k, []), v)[-self.maxlen:]
                self.data[k] = np.append(self.data[k], v)[-self.maxlen:]
                if self.size == 0:
                    if self.data[k][0].dtype == 'float32':
                        newSize += 4 * len(data[k])
                    elif self.data[k][0].dtype == 'float64':
                        newSize += 8 * len(data[k])
                    elif self.data[k][0].dtype == 'int16':
                        newSize += 2 * len(data[k])
                    elif self.data[k][0].dtype == 'int32':
                        newSize += 4 * len(data[k])

        # if we got a vector of data, then we deal with triggering.
        if my_trigger_vector != -1:
            if self.trigger_mode:
                if self.is_triggered:

                    self.samples_after_trig_cnt = self.samples_after_trig_cnt + vector_len
                    if self.samples_after_trig_cnt >= self.samples_after_trig:
                        self.is_triggered = False
                        self.plot_signal_emitter.my_signal.emit()
                        print('emit plot sig')

        self.signal()
        if self.size == 0:
            self.size = newSize
        self.arraysReceived += 1

    def disconnect(self):
        # disconnect cleanly to avoid printing error messages
        self.channel.stopMonitor()
        self.channel.unsubscribe('callback')

    # !! TJM START
    # disconnedct and reconnect only top certain fields to reduce data rate.
    # initially conn to whole pv to get all fields into a list. then gui picks what to graph.
    # when gui changes,we then monitory only those fields.
    def restartMonitor(self, fieldlist):
        print('startMonitor')
        self.channel.stopMonitor()
        reqstr = ''
        reqstr_array = []
        for ff in fieldlist:
            if ff != "None":
                # reqstr = reqstr + '%s,' % ff
                reqstr_array.append(ff)

        if 'ArrayId' in self.pvdatakeys:
            # reqstr = reqstr + 'ArrayId,'
            reqstr_array.append("ArrayId")

        if self.args["TIME_FIELD"] is not None and self.args["TIME_FIELD"] in self.pvdatakeys:
            # reqstr = reqstr + '%s,' % self.args["TIME_FIELD"]
            reqstr_array.append(self.args["TIME_FIELD"])
        if self.args["FREQ_FIELD"] is not None and self.args["FREQ_FIELD"] in self.pvdatakeys:
            # reqstr = reqstr + '%s,' % self.args["FREQ_FIELD"]
            reqstr_array.append(self.args["FREQ_FIELD"])

        # take off last ,
        reqstr = reqstr[:-1]

        # remove duplicated field name
        reqstr_array = list(set(reqstr_array))

        # Setup storage buffer
        changet = self.channel.get(",".join(reqstr_array))
        newData = changet.toDict().items()
        # here we reinit the data mem so we dont have to store everything
        for k, v in newData:
            if type(v) == list:  # should epics v4 lib not have np, we "fix" it by converting list to np
                v = np.array(v)
            if type(v) != np.ndarray: continue
            if len(v) == 0: continue
            self.data[k] = np.array([], dtype=v.dtype)

        # monitor only the fields we want
        self.channel.startMonitor(reqstr)

        # set size to 0 to recalc the data size
        self.size = 0

        # !! TJM END