#!/usr/bin/env python

import argparse
import sys
import time

import numpy as np
import pyqtgraph
try:
    from pyqtgraph.Qt import QtCore, QtWidgets, QtGui
    qwidget = QtWidgets.QWidget
except:
    from pyqtgraph.Qt import QtCore, QtGui
    qwidget = QtGui.QWidget

from pyqtgraph.widgets.RawImageWidget import RawImageWidget

import pvaccess

MAX_FPS = 60


framesDisplayed = 0
gain = None
black = None
lastUpdate = 0
def update(v):
    global framesDisplayed, gain, black, lastUpdate

    # Limt frames per second to below MAX_FPS
    now = time.time()
    if now - lastUpdate < (1./ MAX_FPS): return

    i = v['value'][0]['ubyteValue']
    if not args.noAGC:
        if gain is None:
            black, white = np.percentile(i, [0.01, 99.99])
            gain = 255 / (white - black)
        i = (i - black) * gain
        i = np.clip(i, 0, 255).astype('uint8')

    # resize to get a 2D array from 1D data structure
    i = np.resize(i, (y, x))

    img.setImage(np.flipud(np.rot90(i)))
    app.processEvents()

    if args.benchmark:
        framesDisplayed += 1
        if framesDisplayed > 300:
            app.quit()

    lastUpdate = now

def main():
    global app, img, x, y
    global args

    parser = argparse.ArgumentParser(
            description='AreaDetector video example')

    parser.add_argument('--benchmark', action='store_true',
                        help='measure framerate')
    parser.add_argument('--noAGC', action='store_true',
                        help='disable auto gain')

    parser.add_argument('--channel', metavar='KEY', default=None,
                        help='video image channel name')

    args = parser.parse_args()

    app = QtGui.QApplication([])
    win = qwidget()
    win.setWindowTitle('daqScope')
    layout = QtGui.QGridLayout()
    layout.setMargin(0)
    win.setLayout(layout)
    img = RawImageWidget(win)
    layout.addWidget(img, 0, 0, 0, 0)
    win.show()
    chan = pvaccess.Channel(args.channel)

    x,y = chan.get('field()')['dimension']
    x = x['size']
    y = y['size']
    win.resize(x, y)

    chan.subscribe('update', update)
    chan.startMonitor()

    if args.benchmark:
        start = time.time()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
        chan.stopMonitor()
        chan.unsubscribe('update')
    if args.benchmark:
        stop = time.time()
        print('Frames displayed: %d' % framesDisplayed)
        print('Elapsed time:     %.3f sec' % (stop-start))
        print('Frames per second: %.3f FPS' % (framesDisplayed/(stop-start)))


if __name__ == '__main__':
    main()
