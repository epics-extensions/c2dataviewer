# -*- coding: utf-8 -*-

import argparse
from collections import OrderedDict

from ..utility import PvUtility, PvFieldParameter


class ParamPanel:
    """
    Parameters configuration for side panel of waveform signal display
    """
    def __init__(
        self,
        pvChannelName=None,
        fieldNameChoices=OrderedDict(),
        arrayFieldDict=None,
        **kwargs
    ):
        """
        Initial DaqScope class.

        :param pvChannelName: EPICS 7 channel name
        :param fieldNameChoices: names of interested field in pvChannelName
        :param title: application title
        :param trigger: trigger for scope
        :param trigproto: protocol for trigger PV, 'ca' or 'pva'
        :param samples: default sample numbers
        """
        self.pvChannelName = pvChannelName
        self.fieldNameChoices = fieldNameChoices
        self.arrayFieldDict = arrayFieldDict

        self.DEFAULT_TRIG_PVNAME = kwargs.get("trigger", None)
        self.DEFAULT_TIME_FIELD = kwargs.get("timefield", "Time")
        self.DEFAULT_N_SAMPLES = kwargs.get("samples", 256)

        trigproto = kwargs.get("trigproto", "ca")
        if trigproto is not None:
            self.DEFAULT_TRIG_PVPROTO = str(trigproto).lower()
        else:
            raise ValueError("Protocol for trigger PV cannot be None")
        if self.DEFAULT_TRIG_PVPROTO not in ["ca", "pva"]:
            raise ValueError('Protocol for trigger PV has to be "ca" or "pva"')

        self.configureParser()

    def configure(self, **params):
        if not self.args.pvName:
            raise argparse.ArgumentError("PV Name must be provided")
        if not self.fieldNameChoices and not self.arrayFieldDict:
            self.arrayFieldDict = PvUtility.createDataArrayDict(
                self.args.pvName, self.DEFAULT_SELECT_FIELD_GROUP_SIZE
            )

        self.args.color = self.DEFAULT_COLORS

        mode = "normal"
        if self.args.fft:
            mode = "fft"
        elif self.args.psd:
            mode = "psd"
        elif self.args.diff:
            mode = "diff"
        elif self.args.x_vs_y:
            mode = "x_vs_y"

        if self.args.channels < len(self.args.fieldName):
            self.args.channels = len(self.args.fieldName)
        fieldName = ["None"] * self.args.channels
        for i, n in enumerate(self.args.fieldName):
            fieldName[i] = n

        params = [
            {
                "name": "Acquisition",
                "type": "group",
                "children": [
                    {"name": "PV", "type": "str", "value": self.args.pvName},
                    {"name": "TrigPV", "type": "str", "value": self.args.trigPvName},
                    {"name": "WaitTrigger", "type": "bool", "value": False},
                    {
                        "name": "PostTrigPause",
                        "type": "float",
                        "value": self.args.trigPostPause,
                        "siPrefix": True,
                        "suffix": "s",
                    },
                    {
                        "name": "TrigHoldoff",
                        "type": "float",
                        "value": self.args.trigHoldoff,
                        "siPrefix": True,
                        "suffix": "s",
                    },
                    {"name": "Freeze", "type": "bool", "value": False},
                    {
                        "name": "Buffer",
                        "type": "int",
                        "value": self.args.samples,
                        "siPrefix": True,
                        "suffix": "Samples",
                    },
                ],
            },
            {
                "name": "Display",
                "type": "group",
                "children": [
                    {
                        "name": "Mode",
                        "type": "list",
                        "values": {
                            "Normal": "normal",
                            "FFT": "fft",
                            "PSD": "psd",
                            "Diff": "diff",
                            "X vs Y": "x_vs_y",
                        },
                        "value": mode,
                    },
                    {"name": "Autoscale", "type": "bool", "value": False},
                    {"name": "Histogram", "type": "bool", "value": self.args.histogram},
                    {"name": "Num Bins", "type": "int", "value": self.args.bins},
                    {
                        "name": "Refresh",
                        "type": "float",
                        "value": self.args.refresh / 1000.,
                        "siPrefix": True,
                        "suffix": "s",
                    },
                ],
            },
        ]

        self.fieldNameMap = {}
        for i in range(0, len(fieldName)):
            channelName = "Channel %s" % (i + 1)
            params.append(
                {
                    "name": channelName,
                    "type": "group",
                    "children": [
                        {
                            "name": "Color",
                            "type": "color",
                            "value": self.args.color[i % len(self.args.color)],
                            "readonly": True,
                        },
                        # {'name': 'Field', 'type': 'list', 'values': self.fieldNameChoices, 'value': fieldName[i]},
                        PvFieldParameter(
                            name="Field",
                            fieldNameChoices=self.fieldNameChoices,
                            arrayFieldDict=self.arrayFieldDict,
                            fieldNameMap=self.fieldNameMap,
                            pvName=self.args.pvName,
                        ),
                    ],
                }
            )
        # should be design and organized in a better way
        if self.args.trigPvName is None:
            params.append(
                {
                    "name": "Statistics",
                    "type": "group",
                    "children": [
                        {
                            "name": "Lost Arrays",
                            "type": "int",
                            "value": 0,
                            "readonly": True,
                        },
                        {
                            "name": "Tot. Arrays",
                            "type": "int",
                            "value": 0,
                            "readonly": True,
                            "siPrefix": True,
                        },
                        {
                            "name": "Arrays/Sec",
                            "type": "float",
                            "value": 0.,
                            "readonly": True,
                            "siPrefix": True,
                            "suffix": "/sec",
                        },
                        {
                            "name": "Bytes/Sec",
                            "type": "float",
                            "value": 0.,
                            "readonly": True,
                            "siPrefix": True,
                            "suffix": "/sec",
                        },
                        {
                            "name": "Refresh",
                            "type": "float",
                            "value": 0.,
                            "readonly": True,
                            "siPrefix": True,
                            "suffix": "Frames/sec",
                        },
                    ],
                }
            )
        else:
            params.append(
                {
                    "name": "Statistics",
                    "type": "group",
                    "children": [
                        {
                            "name": "Lost Arrays",
                            "type": "int",
                            "value": 0,
                            "readonly": True,
                        },
                        {
                            "name": "Tot. Arrays",
                            "type": "int",
                            "value": 0,
                            "readonly": True,
                            "siPrefix": True,
                        },
                        {
                            "name": "Arrays/Sec",
                            "type": "float",
                            "value": 0.,
                            "readonly": True,
                            "siPrefix": True,
                            "suffix": "/sec",
                        },
                        {
                            "name": "Bytes/Sec",
                            "type": "float",
                            "value": 0.,
                            "readonly": True,
                            "siPrefix": True,
                            "suffix": "/sec",
                        },
                        {
                            "name": "Refresh",
                            "type": "float",
                            "value": 0.,
                            "readonly": True,
                            "siPrefix": True,
                            "suffix": "Frames/sec",
                        },
                        {
                            "name": "TrigStatus",
                            "type": "str",
                            "value": "",
                            "readonly": True,
                        },
                    ],
                }
            )
