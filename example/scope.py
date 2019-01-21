from math import pi, sin, asin
from time import sleep
import pvaccess as pva
dataStruct =  {'ArrayId': pva.UINT, 'Time': [pva.DOUBLE],
'Sinusoid': [pva.FLOAT], 'Triangle': [pva.FLOAT]}
srv = pva.PvaServer('some_pv', pva.PvObject(dataStruct))
t0 = 0.0
n = 0
dt = 1./1000
while True:
    sleep(0.1)
    time = [t0+dt*i for i in range(0, 100)]
    sinusoid = [sin(2*pi*1.1*t + pi/2) for t in time]
    triangle = [(2/pi)*asin(sin(2*pi*1.1*t)) for t in time]
    pv = pva.PvObject(dataStruct, {'ArrayId': n, 'Time': time,'Sinusoid': sinusoid, 'Triangle': triangle})
    srv.update(pv)
    t0 = time[-1] + dt
    n += 1
