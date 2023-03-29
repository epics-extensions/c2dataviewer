# -*- coding: utf-8 -*-

"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS

Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Example to create example channel using Union type to send data via EPICS7 pvAccess.
It is used to support c2dv development at APS Upgrade.

@author: Guobao Shen <gshen@anl.gov>
"""

import argparse
from math import pi, sin, asin
import time
from time import sleep
import pvaccess as pva


class UnionTest:
    def __init__(self, **kwargs):
        """

        """
        self.dataStruct = {'ArrayId': pva.UINT,
                           'Time': [pva.DOUBLE],
                           'value': pva.PvUnion({'Sinusoid': [pva.FLOAT], 'Triangle': [pva.DOUBLE]}),
                           'Sinusoid': [pva.FLOAT],
                           'Triangle': [pva.FLOAT]}

        self.counts = 0
        step = kwargs.get("sample", 1000)
        self.time_interval = 1. / step

        self.pv = pva.PvObject(self.dataStruct)
        self.pvaServer = pva.PvaServer('{}:Scope:Data'.format(kwargs.get("pv", "Test")), self.pv)
        print("PV Name: {}:Union:Data".format(kwargs.get("pv", "Test")))

    def update(self):
        # sleep(0.1)
        time0 = time.time()
        ts = [time0 + self.time_interval * i for i in range(0, 100)]
        sinusoid = [sin(2 * pi * 1.1 * t + pi / 2) for t in ts]
        triangle = [(2 / pi) * asin(sin(2 * pi * 1.1 * t)) for t in ts]

        pv = pva.PvObject(self.dataStruct, {'ArrayId': self.counts,
                                            'Time': ts,
                                            'value': {'Sinusoid': sinusoid},
                                            'Sinusoid': sinusoid,
                                            'Triangle': triangle})
        self.pvaServer.update(pv)
        self.counts = self.counts + 1


def main():
    """
    Scope simulator main routine

    :return:
    """
    parser = argparse.ArgumentParser(
        description='Example using EPICS7 Union with pvaPy to provide data via EPICS7 pvAccess')

    parser.add_argument('--pv', type=str, default="Test",
                        help='EPICS PV name prefix. The full PV name will be {prefix}:Scope:Data'
                             'e.g. --pv=test, the full PV name will be "test:Scope:Data"')
    parser.add_argument('--freq', type=int, default=10,
                        help='data update frequency')
    parser.add_argument('--sample', type=int, default=1000,
                        help='data samples in 1 second')

    args = parser.parse_args()

    pvas = UnionTest(pv=args.pv, sample=args.sample)

    while True:
        pvas.update()
        sleep(1./args.freq)

if __name__ == "__main__":
    main()
