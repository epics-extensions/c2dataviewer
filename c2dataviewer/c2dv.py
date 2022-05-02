
# -*- coding: utf-8 -*-

"""
Copyright 2018 UChicago Argonne LLC
 as operator of Argonne National Laboratory

PVA object viewer utilities

@author: Guobao Shen <gshen@anl.gov>
"""


import os
import sys
import pkg_resources
import argparse
from configparser import ConfigParser
import enum
import logging

class AppType(enum.Enum):
    SCOPE = "scope"
    IMAGE = "image"
    STRIPTOOL = "striptool"

    def __str__(self):
        return self.value

def qxl_module_loaded():
    fn = "/proc/modules"
    if not os.path.isfile(fn):
        return False
    with open(fn, "r") as f:
        modules = f.readlines()
    return any([m for m in modules if m.startswith("qxl")])

# Suppress libGL error about swrast when running
# on a VM with paravirtual graphics driver (qxl).
# Run before any qt code runs
if qxl_module_loaded():
    os.environ['LIBGL_ALWAYS_INDIRECT'] = 'true'

# Limit numpy to a single thread
# Must run before numpy import
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

# Get the version number used by setup.py at package build time
try:
    __version__ = pkg_resources.get_distribution('C2DataViewer').version
except pkg_resources.DistributionNotFound:
    __version__ = 'Unknown'


def load_config(N=None):
    """
    Load default configuration from configuration file

    :return:
    """
    import os.path
    pkgcfg = os.path.join( os.path.dirname(__file__), 'c2dv.cfg' )
    cfgfile = ['/etc/c2dv.cfg', os.path.expanduser('~/.c2dvrc'), 'c2dv.cfg', pkgcfg]
    # if N is not None:
    #     cfgfile.append(N)

    noconfig = True
    for cfg in cfgfile:
        if os.path.isfile(cfg):
            noconfig=False
            break

    if noconfig:
        raise RuntimeError("No configuration file found.")
    cf = ConfigParser()
    if N is not None:
        if not os.path.isfile(N):
            raise RuntimeError("%s not found." % (N))
        cf.read(N)
    else:
        cf.read(cfgfile)
    return cf


def pvmaps(pvs, alias=None):
    """

    :param pvs:
    :param alias:
    :return:
    """
    pvmap = {}
    # labels = []
    if alias is not None:
        ALIAS = alias.split(",")
        for idx, pv in enumerate(pvs.split(",")):
            pv = pv.strip()
            if pv != "":
                if idx < len(ALIAS) and ALIAS[idx].strip() != "":
                    pvmap[ALIAS[idx].strip()] = pv.strip()
                else:
                    pvmap[pv.strip()] = pv.strip()
    else:
        for pv in pvs.split(","):
            pvmap[pv.strip()] = pv.strip()
    return pvmap


def main():
    """

    :return:
    """
    parser = argparse.ArgumentParser(
            description='C2DataViewer for EPICS7 PVStructure Data display via pvAccess')

    parser.add_argument('--app', type=AppType,
                        help='Application name', choices=list(AppType))
    # TODO: add CLI interface later to over write configuration
    parser.add_argument('--config', type=str,
                        help='configuration file')
    parser.add_argument('--pv', type=str,
                        help='EPICS PV names. Support multiple PVs which are comma separated.'
                             ' e.g. PV1,PV2,PV3')
    parser.add_argument('--alias', type=str,
                        help='EPICS PV alias names. Support multiple alias name which are comma separated.'
                             ' e.g. name1,name2,name3')
    parser.add_argument('--arrayid', type=str,
                        help='EPICS PV field name for ID for scope application, '
                             'which is used by scope to count losing arrays.'
                             ' e.g. ArrayId')
    parser.add_argument('--xaxes', type=str,
                        help='EPICS PV field name to be used for x axes for scope application.'
                             ' e.g. Time')
    parser.add_argument('--max', type=float, default=None,
                        help='Filter out values greater than MAX')
    parser.add_argument('--min', type=float, default=None,
                        help='Filter out values less than MIN')
    parser.add_argument('--trigger', type=str, default=None,
                        help='Trigger PV for scope. Format: [proto://]pv_name. '
                             'Protocol is optional, and needs to be either "ca" or "pva" when specified, '
                             'by default, uses EPICS7 pvAccess.'
                             ' e.g. ca://MY:TEST:TRIG:PV or MY:TEST:TRIG:PV')
    parser.add_argument(
        "--debug",
        action='store_true',
        help="Turn on debug messages"
    )

    args = parser.parse_args()

    level = logging.WARNING

    if args.debug:
        level = logging.DEBUG
        
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s %(levelname)-6s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    cfg = load_config(args.config)

    pv_map = None
    if args.pv is not None:
        pv_map = pvmaps(args.pv, args.alias)

    app = args.app
    if args.app is None:
        app = AppType(cfg["DEFAULT"]["APP"].lower())
        
    if app == AppType.IMAGE:
        from c2dataviewer import imagev
        # application from CLI overwrite the one in configuration file
        section = cfg[cfg["DEFAULT"]["APP"]]["SECTION"]
        if pv_map is None:
            # use pv information from configuration file
            try:
                ALIAS = cfg[section]["ALIAS"]
            except KeyError:
                ALIAS = None
            try:
                pvnames = cfg[section]["PV"]
            except KeyError:
                pvnames = None
            pv_map = pvmaps(pvnames, ALIAS)
        try:
            scale = float(cfg[section]["SCALE"])
        except KeyError:
            scale = 1.0
        try:
            noAGC = True if cfg[section]["AUTOGAIN"] == 'DISABLED' else False
        except KeyError:
            noAGC = False
        imagev(pv_map, list(pv_map.keys()), scale, noAGC)
    elif app == AppType.SCOPE:
        from c2dataviewer import scope
        scope(cfg, pv=pv_map, arrayid=args.arrayid, xaxes=args.xaxes,
              max=args.max, min=args.min, trigger=args.trigger)
    elif app == AppType.STRIPTOOL:
        from c2dataviewer import striptool
        striptool(cfg, pv=pv_map)
    else:
        raise RuntimeError("Unknown application ({0})".format(args.app))


if __name__ == "__main__":
    main()
