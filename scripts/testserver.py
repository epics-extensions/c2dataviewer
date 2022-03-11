import pvaccess as pva
import argparse
import multiprocessing as mp
import random
import time

def run_striptool_pvserver(pvname):
    schema = {'value':pva.FLOAT}
    server = pva.PvaServer(pvname, pva.PvObject(schema))
    delay = random.uniform(0.1, 5)
    print('starting %s at %f Hz' % (pvname, 1/delay))
    while(True):
        value = random.uniform(0, 100)
        pv = pva.PvObject(schema, {'value':value})
        server.update(pv)
        time.sleep(delay)

    
def run_striptool(pvnames):
    with mp.Pool(len(pvnames)) as p:
        p.map(run_striptool_pvserver, pvnames)

def run_scope(pvname):
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
    striptool.add_argument('pvnames', nargs='+', help='scalar pv(s) to host')
    scope = subparsers.add_parser('scope', help='Test server for scope app')
    scope.add_argument('pvname', help='structure pv to host')
    args = parser.parse_args()
    if args.command == 'striptool':
        run_striptool(args.pvnames)
    elif args.command == 'scope':
        run_scope(args.pvname)
