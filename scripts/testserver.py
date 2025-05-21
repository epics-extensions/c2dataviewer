"""
C2 DATA VIEWER is distributed subject to a Software License Agreement found
in the file LICENSE that is included with this distribution.
SPDX-License-Identifier: EPICS
"""

import pvaccess as pva
import argparse
import multiprocessing as mp
import random
import time
import enum

class WaveformType(enum.Enum):
    RANDOM = 'random'
    LINEAR = 'linear'

    def __str__(self):
        return self.value

class LinearGenerator:
    def __init__(self, offset, size):
        self.offset = offset
        self.x = 0
        self.size = size
    def calc(self):
        self.x += 1
        self.x = self.x % self.size
        return self.x + self.offset

class RandomGenerator:
    def __init__(self):
        pass
    
    def calc(self):
        return random.uniform(0, 100)

class Trigger:
    def __init__(self, args):
        self.pvname = args.triggerpv
        self.schema = {'value': pva.FLOAT,
                       'timeStamp' : {
                           'secondsPastEpoch' : pva.UINT,
                           'nanoseconds' : pva.UINT
                       }
                       }
        self.server = pva.PvaServer(self.pvname, pva.PvObject(self.schema))
        self.delay = args.trigger_interval
        self.gen = LinearGenerator(-10, 20)

    def fire(self, trigger_time):
        value = self.gen.calc()
        ts = int(trigger_time)
        tns = (trigger_time - ts)*1e9
        pv = pva.PvObject(self.schema, {'value':value,
                                        'timeStamp' :
                                        { 'secondsPastEpoch' : ts, 'nanoseconds' : int(tns) } })
        self.server.update(pv)

    
def run_striptool_pvserver(arg):
    pvid = arg[0]
    args = arg[1]    
    pvname = args.pvprefix + str(pvid)
    maxdelay = 1 / args.minrate
    make_struct = args.num_structs and pvid < args.num_structs
    if make_struct:
        print('creating %s as a struct PV' % pvname)
        schema = { 'obj1' : {'x': pva.FLOAT, 'y': pva.FLOAT}, 'z': pva.FLOAT}
    else:
        schema = {'value':pva.FLOAT}
    server = pva.PvaServer(pvname, pva.PvObject(schema))
    delay = random.uniform(0.1, maxdelay)
    print('starting %s at %f Hz' % (pvname, 1/delay))
    wftype = arg[1].wftype
    if wftype == WaveformType.LINEAR:
        offset = random.uniform(0, 100)
        size = random.uniform(100, 5000);
        gen = LinearGenerator(offset, size)
    else:
        gen = RandomGenerator()
        
    while(True):
        value = gen.calc()

        if make_struct:
            pvval = {'obj1': {'x': value, 'y': -value }, 'z': value + 10 }
        else:
            pvval = {'value': value}
            
        pv = pva.PvObject(schema, pvval)
        server.update(pv)
        time.sleep(delay)

    
def run_striptool(args):
    with mp.Pool(args.numpvs) as p:
        arglist = [ (c, args) for c in range(args.numpvs) ]
        p.map(run_striptool_pvserver, arglist)

def trigger_process(args):
    pvname = args.triggerpv
    trigger = Trigger(args)
    print('trigger %s started' % (pvname))
    while(True):
        trigger.fire(time.time())
        time.sleep(args.trigger_interval)
    
def run_scope(args):
    if args.triggerpv:
        p = mp.Process(target=trigger_process, args=(args,))
        p.start()
        
    pvname = args.pvname
    schema = { 'obj1' : {'x': [pva.FLOAT], 'y': [pva.FLOAT]}, 'obj2' : {'x': [pva.FLOAT], 'y': [pva.FLOAT]}, 'time': [pva.DOUBLE], 'objectTime': pva.DOUBLE, 'names': [pva.STRING]}
    server = pva.PvaServer(pvname, pva.PvObject(schema))
    print('starting', pvname)
    delay = 1/args.pvrate
    nsamples = args.wflen
    sample_time_interval = delay / nsamples
    while(True):
        objectTime = float(time.time())
        time.sleep(delay)
        times = [ i*sample_time_interval + objectTime for i in range(0, nsamples) ]
        x = [ random.uniform(-i, i) for i in range(0, nsamples) ]
        y = [ random.uniform(-i, i) for i in range(0, nsamples) ]
        names = [ 'val'+str(i) for i in range(0, nsamples) ]
        pv = pva.PvObject(schema, {'obj1':{'x':x, 'y':y}, 'obj2': {'x':x, 'y':y},
                                   'objectTime': objectTime, 'time' : times, 'names': names})
        server.update(pv)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser('Test server')
    subparsers = parser.add_subparsers(dest='command')
    striptool = subparsers.add_parser('striptool', help='Test server for striptool app')
    striptool.add_argument('pvprefix',  help='prefix to generated pv names')
    striptool.add_argument('numpvs',  help='number of pvs to generate', type=int)
    striptool.add_argument('--min-rate', dest='minrate', default=0.5, type=int)
    striptool.add_argument('--waveform-type', dest='wftype', default=WaveformType.RANDOM, type=WaveformType, choices=list(WaveformType))
    striptool.add_argument('--add-struct', dest='num_structs', type=int, help='If set, number of pvs to be struct instead of scalar')
    scope = subparsers.add_parser('scope', help='Test server for scope app')
    scope.add_argument('pvname', help='structure pv to host')
    scope.add_argument('--trigger-pv', help='Adds a trigger PV.  PV values will range between -10 and 10', dest='triggerpv')
    scope.add_argument('--trigger-interval', help='Fires at given interval in seconds', dest='trigger_interval', default=1, type=float)
    scope.add_argument('--pv-rate', help='PV update rate', dest='pvrate', default=2, type=float)
    scope.add_argument('--waveform-length', help='Waveform length', dest='wflen', default=100, type=int)    
    args = parser.parse_args()
    if args.command == 'striptool':
        run_striptool(args)
    elif args.command == 'scope':
        run_scope(args)
