# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

"""
import sys

import argparse

from ..utility import PvUtility
from ..utility import PvFieldParameter


class Configure:
    """

    """
    def __init__(self, params):
        """

        :param params: parameters parsed from command line and configuration file
        """
        self.params = params

    def configureApp(self):
        """

        :return: paramcfg: UI display parameter configuration
        """
        if not self.params["PV"]:
            raise RuntimeError("EPICS PV name must be provided")

        if not self.params["FIELD_NAMES"] and not self.params["ARRAY_FIELD"]:
            self.params['ARRAY_FIELD'] = PvUtility().createDataArrayDict(self.params["PV"],
                                                                         self.params["FIELD_GROUP_SIZE"])

        mode = self.params["ALGORITHM"]

        fieldName = ["None"] * self.params['N_CHANNELS']
        if self.params['FIELD'] is not None:
            for i, n in enumerate(self.params['FIELD']):
                fieldName[i] = n

        trigPvName = None
        try:
            trigPvName = self.params["TRIGGER"]["PV"]
        except KeyError:
            pass

        paramcfg = [
            {"name": "Acquisition", "type": "group", "children": [
                {"name": "PV", "type": "str", "value": self.params["PV"]},
                {"name": "TrigPV", "type": "str", "value": trigPvName},
                {"name": "WaitTrigger", "type": "bool", "value": False},
                {"name": "Freeze", "type": "bool", "value": False},
                {"name": "Buffer", "type": "int", "value": self.params['N_SAMPLES'], "siPrefix": True,
                 "suffix": "Samples"},
            ]},

            {"name": "Display", "type": "group", "children": [
                {"name": "Mode", "type": "list", "values": {
                    "Normal": "normal",
                    "FFT": "fft",
                    "PSD": "psd",
                    "Diff": "diff",
                    "X vs Y": "x_vs_y",
                }, "value": mode},
                {"name": "Autoscale", "type": "bool", "value": False},
                {"name": "Histogram", "type": "bool", "value": self.params["HISTOGRAM"]},
                {"name": "Num Bins", "type": "int", "value": self.params["N_BINS"]},
                {"name": "Refresh", "type": "float", "value": self.params["REFRESH_RATE"] / 1000., "siPrefix": True,
                 "suffix": "s"},
            ]}
        ]

        self.fieldNameMap = {}
        for i in range(0, len(fieldName)):
            channelName = "Channel %s" % (i + 1)
            paramcfg.append(
                {"name": channelName,
                 "type": "group",
                 "children": [
                     {
                         "name": "Color",
                         "type": "color",
                         "value": self.params["COLOR"][i % len(self.params["COLOR"])],
                         "readonly": True
                     },
                     # {"name": "Field", "type": "list", "values": self.fieldNameChoices, "value": fieldName[i]},
                     PvFieldParameter(name="Field",
                                      fieldNameChoices=self.params['FIELD_NAMES'],
                                      arrayFieldDict=self.params['ARRAY_FIELD'],
                                      fieldNameMap=self.fieldNameMap,
                                      pvName=self.params["PV"]
                                      ),
                 ]
                 }
            )
        # should be design and organized in a better way
        if trigPvName is None:
            paramcfg.append({"name": "Statistics", "type": "group", "children": [
                {"name": "Lost Arrays", "type": "int", "value": 0, "readonly": True},
                {"name": "Tot. Arrays", "type": "int", "value": 0, "readonly": True, "siPrefix": True},
                {"name": "Arrays/Sec", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
                 "suffix": "/sec"},
                {"name": "Bytes/Sec", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
                 "suffix": "/sec"},
                {"name": "Refresh", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
                 "suffix": "Frames/sec"},
            ]})
        else:
            paramcfg.append({"name": "Statistics", "type": "group", "children": [
                {"name": "Lost Arrays", "type": "int", "value": 0, "readonly": True},
                {"name": "Tot. Arrays", "type": "int", "value": 0, "readonly": True, "siPrefix": True},
                {"name": "Arrays/Sec", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
                 "suffix": "/sec"},
                {"name": "Bytes/Sec", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
                 "suffix": "/sec"},
                {"name": "Refresh", "type": "float", "value": 0., "readonly": True, "siPrefix": True,
                 "suffix": "Frames/sec"},
                {"name": "TrigStatus", "type": "str", "value": "", "readonly": True},
            ]})

        return paramcfg