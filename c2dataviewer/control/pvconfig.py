import random
from ..model import *

def randcolor():
    return "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])


class PvConfig:
    default_colors = ['#FFFF00', '#FF00FF', '#55FF55', '#00FFFF', '#5555FF',
                      '#5500FF', '#FF5555', '#0000FF', '#FFAA00', '#000000']
    color_index = 0
    
    def __init__(self, pvname=None, color=None, proto=None):
        self.pvname = pvname
        if color:
            self.color = color
        elif PvConfig.color_index < len(PvConfig.default_colors):
            self.color = PvConfig.default_colors[PvConfig.color_index]
            PvConfig.color_index += 1
        else:
            self.color = randcolor()

        self.set_proto(proto)

    def set_proto(self, pname):
        self.proto = make_protocol(pname) if pname is not None else pname        

        

