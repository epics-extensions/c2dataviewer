# -*- coding: utf-8 -*-

"""
Copyright 2017 UChicago Argonne LLC
 as operator of Argonne National Laboratory

This application is developed to view structured data from EPICS system.

@author: Guobao Shen <gshen@anl.gov>
"""

import logging
import sys
from  argparse import ArgumentParser

from pvaviewer.widgets import Scope

_log = logging.getLogger("pvaviewer")


def paramparser():
    """
    Parse command line parameters.

    :return:
    """
    par = ArgumentParser(description="Real-time PVA Structure Data Displaying.")

    # General options
    par.add_argument("-v", "--version", action="store_true",
                   help="Show version number")
    par.add_argument("-d", "--debug", action="store_true", default=False,
                   help="Debugging mode")
    par.add_argument("-c", "--config", metavar="KEY", default=None,
                   help="Configuration file for PVA viewer.")
    par.add_argument("--verbose", action="count", default=0,
                   help="Get more details information/logging")
    par.add_argument("--pv", metavar="NAME",
                   help="PV name")
    par.add_argument("--field", type=str, nargs="*", default=None,
                   help="PV structure field names")
    par.add_argument("--trigger",metavar="TRIGNAME",
                   help="Trigger PV name")
    par.add_argument("--trigproto",type=float,default=None,
                   help="Communication prototol for trigger")
    par.add_argument("--trighold",type=float,default=None,
                   help="ignore triggers for seconds")
    par.add_argument("--postpause", type=float, default=None,
                   help="pause for seconds after trigger is done")
    par.add_argument("--noc", type=int, metavar="N",
                   help="Number of channels to display")
    par.add_argument("--samples", type=int, metavar="N",
                   help="Number of samples to display")
    par.add_argument("--rate", type=int, metavar="N",
                   help="Refresh rate in ms")
    par.add_argument("--max", type=float, default=None,
                   help="Filter out values greater than MAX")
    par.add_argument("--min", type=float, default=None,
                   help="Filter out values less than MIN")
    par.add_argument("--algorithm", default=None, action="store_true",
                   help="Algorithm for plotting: normal, FFT, PSD, XvsY")
    par.add_argument("-t", "--timefield", type=str, metavar="NAME",
                   help="Sample Time field name")
    par.add_argument("-f", "--freqfield", type=str, default=None, metavar="NAME",
                   help="Sample Frequency field name")
    par.add_argument("--periodfield", type=str, default=None, metavar="NAME",
                   help="Sample Period field name")
    par.add_argument("--timestamp", type=str, default=None, metavar="NAME",
                   help="timestamp field name (Seconds Past Epoch)")
    par.add_argument("--diff", action="store_true",
                   help="Plot discrete differences of field names")
    par.add_argument("--histogram", action="store_true", default=False,
                   help="Plot histogram of field names")
    par.add_argument("--bins", type=int,
                   help="Number of histogram bins")
    par.add_argument("--width", type=int,
                   help="Window width in px")
    par.add_argument("--height", type=int,
                   help="Window height in px")

    return par.parse_args()


def main():
    """
    Main function of PVA Structure Display.

    :return:
    """
    opt = paramparser()

    if opt.version:
        from pvaviewer import __version__
        print (__version__)
        sys.exit(0)

    LVL = {0: logging.WARN, 1: logging.INFO, 2: logging.DEBUG}
    logging.basicConfig(format="%(message)s", level=LVL.get(opt.verbose, LVL[2]))

    from pvaviewer.config import load_config
    cfg = load_config(opt.config)

    a = Scope(cfg=cfg, opt=opt)
    a.run()

if __name__ == "__main__":
    main()
