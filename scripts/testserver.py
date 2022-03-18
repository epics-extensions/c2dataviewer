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
    def __init__(self):
        self.offset = random.uniform(0, 100)
        self.x = 0
        self.size = random.uniform(100, 5000)
    def calc(self):
        self.x += 1
        self.x = self.x % self.size
        return self.x + self.offset

class RandomGenerator:
    def __init__(self):
        pass
    
    def calc(self):
        return random.uniform(0, 100)
    
def run_striptool_pvserver(arg):
    pvname = arg[1].pvprefix + str(arg[0])
    maxdelay = 1 / arg[1].minrate
    schema = {'value':pva.FLOAT}
    server = pva.PvaServer(pvname, pva.PvObject(schema))
    delay = random.uniform(0.1, maxdelay)
    print('starting %s at %f Hz' % (pvname, 1/delay))
    wftype = arg[1].wftype
    if wftype == WaveformType.LINEAR:
        gen = LinearGenerator()
    else:
        gen = RandomGenerator()
        
    while(True):
        value = gen.calc()
        pv = pva.PvObject(schema, {'value':value})
        server.update(pv)
        time.sleep(delay)

    
def run_striptool(args):
    with mp.Pool(args.numpvs) as p:
        arglist = [ (c, args) for c in range(args.numpvs) ]
        p.map(run_striptool_pvserver, arglist)

def run_scope(args):
    pvname = args.pvname
    schema = { 'obj1' : {'x': [pva.FLOAT], 'y': [pva.FLOAT]}, 'obj2' : {'x': [pva.FLOAT], 'y': [pva.FLOAT]}}
    server = pva.PvaServer(pvname, pva.PvObject(schema))
    print('starting', pvname)
    while(True):
        x = [ random.uniform(-i, i) for i in range(0, 100) ]
        y = [ random.uniform(-i, i) for i in range(0, 100) ]
        pv = pva.PvObject(schema, {'obj1':{'x':x, 'y':y}, 'obj2': {'x':x, 'y':y}})
        server.update(pv)
        time.sleep(0.5)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser('Test server')
    subparsers = parser.add_subparsers(dest='command')
    striptool = subparsers.add_parser('striptool', help='Test server for striptool app')
    striptool.add_argument('pvprefix',  help='prefix to generated pv names')
    striptool.add_argument('numpvs',  help='number of pvs to generate', type=int)
    striptool.add_argument('--min-rate', dest='minrate', default=0.5, type=int)
    striptool.add_argument('--waveform-type', dest='wftype', default=WaveformType.RANDOM, type=WaveformType, choices=list(WaveformType))
    scope = subparsers.add_parser('scope', help='Test server for scope app')
    scope.add_argument('pvname', help='structure pv to host')
    args = parser.parse_args()
    if args.command == 'striptool':
        run_striptool(args)
    elif args.command == 'scope':
        run_scope(args)
