# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Scope simulator which provides scope data via EPICS7 pvAccess for APS Upgrade DAQ system.
It is used to support c2dv development at APS Upgrade.

@author: Guobao Shen <gshen@anl.gov>
"""

import argparse
from math import pi, sin, asin
from time import sleep
import pvaccess as pva


class ScopeServer:
    def __init__(self, **kwargs):
        """

        """
        self.dataStruct = {'ArrayId': pva.UINT,
                           'Time': [pva.DOUBLE],
                           'Sinusoid': [pva.FLOAT],
                           'Triangle': [pva.FLOAT]}

        self.time0 = 0.0
        self.counts = 0
        step = kwargs.get("sample", 1000)
        self.time_interval = 1. / step

        self.pv = pva.PvObject(self.dataStruct)
        self.pvaServer = pva.PvaServer('{}:Scope:Data'.format(kwargs.get("pv", "Test")), self.pv)
        print("PV Name: {}:Scope:Data".format(kwargs.get("pv", "Test")))

    def update(self):
        # sleep(0.1)
        time = [self.time0 + self.time_interval * i for i in range(0, 100)]
        sinusoid = [sin(2 * pi * 1.1 * t + pi / 2) for t in time]
        triangle = [(2 / pi) * asin(sin(2 * pi * 1.1 * t)) for t in time]

        pv = pva.PvObject(self.dataStruct, {'ArrayId': self.counts,
                                            'Time': time,
                                            'Sinusoid': sinusoid,
                                            'Triangle': triangle})
        self.pvaServer.update(pv)

        # self.pv.set({'ArrayId': self.counts,
        #              'Time': time,
        #              'Sinusoid': sinusoid,
        #              'Triangle': triangle})
        # self.pvaServer.update(self.pv)

        # self.pv.set({'ArrayId': self.counts})
        # self.pv.set({'Time': time})
        # self.pv.set({'Sinusoid': sinusoid})
        # self.pv.set({'Triangle': triangle})
        # self.pvaServer.update(self.pv)

        self.time0 = time[-1] + self.time_interval
        self.counts = self.counts + 1


def main():
    """
    Scope simulator main routine

    :return:
    """
    parser = argparse.ArgumentParser(
        description='Scope provider to simulate APSU DAQ and provide data via EPICS7 pvAccess')

    parser.add_argument('--pv', type=str, default="Test",
                        help='EPICS PV name prefix. The full PV name will be {prefix}:Scope:Data'
                             'e.g. --pv=test, the full PV name will be "test:Scope:Data"')
    parser.add_argument('--freq', type=int, default=10,
                        help='data update frequency')
    parser.add_argument('--sample', type=int, default=1000,
                        help='data samples in 1 second')

    args = parser.parse_args()

    pvas = ScopeServer(pv=args.pv, sample=args.sample)

    while True:
        pvas.update()
        sleep(1./args.freq)

if __name__ == "__main__":
    main()