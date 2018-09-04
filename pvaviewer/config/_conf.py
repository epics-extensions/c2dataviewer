# -*- coding: utf-8 -*-

"""
Copyright 2017 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""


from configparser import ConfigParser


def load_config(n):
    """
    Load default configuration from configuration file

    :param n:
    :return:
    """
    import os.path
    cfgfile = ['/etc/pvaviewer.cfg', os.path.expanduser('~/.pvaviewerrc'), 'pvaviewer.cfg']
    if n is not None:
        cfgfile.append(n)

    noconfig = True
    for cfg in cfgfile:
        if os.path.isfile(cfg):
            noconfig=False
            break

    if noconfig:
        raise RuntimeError("No configuration file found.")

    dflt = {"DEFAULT_SAMPLE": 256,
            "DEFAULT_N_CHANNELS": 4,
            "DEFAULT_N_BINS": 100,
            # Default refresh rate in millisecond
            "DEFAULT_REFRESH_RATE_MS": 100,
            "DEFAULT_WINDOW_WIDTH_PX": 640,
            "DEFAULT_WINDOW_HEIGHT_PX": 480,
            # Default color definition, y: yellow, m: magenta, g: green, c: cyan, r: red
            # "DEFAULT_COLORS": ["y", "m", "g", "c", "b", "r"],
            "DEFAULT_COLORS": ['#ffff00', '#ff00ff', '#55ff55', '#00ffff', '#5555ff', '#ff5555'],
            "DEFAULT_SELECT_FIELD_GROUP_SIZE": 10,
            # Supported algorithm beyond normal display, XvY is to plot X against Y
            "ALGORITHM": ["FFT", "PSD", "DIFF", "XvsY"],
            "DEFAULT_SELECT_FIELD_GROUP_SIZE": 10
            }


    cf = ConfigParser(defaults=dflt)

    cf.read(cfgfile)

    return cf
