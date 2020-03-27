# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Image Simulator which provides image data via EPICS7 pvAccess.
It is used to support c2dv development at APS Upgrade.

@author: Guobao Shen <gshen@anl.gov>
"""

import time
import argparse
import numpy as np
import pvaccess


class ImageServer:
    def __init__(self, **kwargs):
        """

        """
        self.vidData = {
            'value': ({'ubyteValue': [pvaccess.UBYTE],
                       'byteValue': [pvaccess.BYTE]},),

            'codec': {'name': pvaccess.STRING,
                      'parameters': ()},

            'compressedSize': pvaccess.LONG,
            'uncompressedSize': pvaccess.LONG,

            'dimension': [{'size': pvaccess.INT,
                           'offset': pvaccess.INT,
                           'fullSize': pvaccess.INT,
                           'binning': pvaccess.INT,
                           'reverse': pvaccess.BOOLEAN}],

            'uniqueId': pvaccess.INT,

            'dataTimeStamp': {'secondsPastEpoch': pvaccess.LONG,
                              'nanoseconds': pvaccess.INT,
                              'userTag': pvaccess.INT},

            'attribute': [{'name': pvaccess.STRING,
                           'value': (),
                           'descriptor': pvaccess.STRING,
                           'sourceType': pvaccess.INT,
                           'source': pvaccess.STRING}],

            'descriptor': pvaccess.STRING,

            'alarm': {'severity': pvaccess.INT,
                      'status': pvaccess.INT,
                      'message': pvaccess.STRING},

            'timeStamp': {'secondsPastEpoch': pvaccess.LONG,
                          'nanoseconds': pvaccess.INT,
                          'userTag': pvaccess.INT},

            'display': {'limitLow': pvaccess.DOUBLE,
                        'limitHigh': pvaccess.DOUBLE,
                        'description': pvaccess.STRING,
                        'format': pvaccess.STRING,
                        'units': pvaccess.STRING},
        }

        self.counts = 0
        self.X = kwargs.get("X", 640)
        self.Y = kwargs.get("Y", 480)
        self.FPS = kwargs.get("FPS", 30)
        self.pvprefix = kwargs.get("PV", "Test")

        self.xdim = None
        self.ydim = None
        self.attr = None
        self.pv = None
        self.pvaServer = None
        self.frames = None

        self.config()

    def config(self):
        """

        :return:
        """
        self.pv = pvaccess.PvObject(self.vidData)
        self.pvaServer = pvaccess.PvaServer('{}:Pva1:Image'.format(self.pvprefix), self.pv)
        print("PV Name: {}:Pva1:Image".format(self.pvprefix))
        self.xdim = {'size': self.X, 'fullSize': self.X, 'reverse': False, 'binning': 1}
        self.ydim = {'size': self.Y, 'fullSize': self.Y, 'reverse': False, 'binning': 1}
        self.attr = {'name': 'ColorMode', 'descriptor': 'Color mode',
                     'sourceType': 0, 'source': 'Driver'}

        self.frames = np.zeros((self.FPS+1, self.X * self.Y), np.uint8)
        for i in range(self.FPS+1):
            self.frames[i] = np.random.normal(127, 64, self.X * self.Y).astype('uint8')

    def update(self):
        self.pv.set({'value': ({'ubyteValue': list(self.frames[self.counts % (self.FPS + 1)])},), })
        self.pv.set({'dimension': [self.xdim, self.ydim]})
        self.pv.set({'attribute': [self.attr]})
        s, ns = divmod(time.time(), 1)
        self.pv.set({'timeStamp': {'secondsPastEpoch': int(s),
                                   'nanoseconds': int(ns*1e9),
                                   'userTag': 0}})
        self.pvaServer.update(self.pv)
        self.counts = self.counts + 1


def main():
    """
    Image simulator main routine

    :return:
    """
    parser = argparse.ArgumentParser(
        description='Image provider to simulate AD and provide data via EPICS7 pvAccess')

    parser.add_argument('--pv', type=str, default="Test",
                        help='EPICS PV name prefix. The full PV name will be {prefix}:Pva1:Image'
                             'e.g. --pv=test, the full PV name will be "test:Pva1:Image"')
    parser.add_argument('--x', type=int, default=640,
                        help='Horizontal image size, 640 by default')
    parser.add_argument('--y', type=int, default=480,
                        help='Vertical image size, 480 by default')
    parser.add_argument('--fps', type=int, default=30,
                        help='Frame rate per second, 30 by default')

    args = parser.parse_args()

    pvas = ImageServer(X=args.x, Y=args.y, FPS=args.fps, PV=args.pv)

    while True:
        pvas.update()
        time.sleep(1./args.fps)

if __name__ == "__main__":
    main()
