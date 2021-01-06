# -*- coding: utf-8 -*-

"""
Copyright 2020 UChicago Argonne LLC
 as operator of Argonne National Laboratory

Helper functions for c2d unit tests.

@author: Matic Pogacnik <mpogacnik@anl.gov>
"""
import numpy as np
import pvaccess as pva


############################################
# ND Image
############################################
def get_time_stamp(time_stamp=None):
    """
    Transform seconds to PVA timestamp (or generate for the current time if time_stamp=None)

    :param time_stamp: (int) Timestamp in nano seconds or None to take current time.
    :return: (PvTimeStamp) Timestramp value.
    """
    NANOSECONDS_IN_SECOND = 1000000000
    if time_stamp is None:
        time_stamp = np.datetime64(dt.now(), 'ns')
    else:
        time_stamp = np.datetime64(time_stamp, 'ns')
    t = (time_stamp-np.datetime64(0,'ns'))/np.timedelta64(1, 's')
    s = int(t)
    ns = int((t - s)*NANOSECONDS_IN_SECOND)
    return pva.PvTimeStamp(s,ns,0)

def create_image(id, image=None, nx=None, ny=None, color_mode=None, time_stamp=None, extra_fields_PV_object=None):
    """
    Generate image as NtNdArray.

    :param id: (int) Array index.
    :param nx: (int) Image
    """
    # Generate timestamp and the image
    time_stamp = get_time_stamp(time_stamp)
    if image is None:
        image = np.random.randint(0,256, size=nx*ny, dtype=np.uint8)

    # Build the NtNdArray
    if extra_fields_PV_object:
        nda = pva.NtNdArray(extra_fields_PV_object.getStructureDict())
    else:
        nda = pva.NtNdArray()
    nda['uniqueId'] = id
    dims = [pva.PvDimension(nx, 0, nx, 1, False), pva.PvDimension(ny, 0, ny, 1, False)]
    nda['codec'] = pva.PvCodec('pvapyc', pva.PvInt(14))
    nda['dimension'] = dims
    nda['descriptor'] = 'PvaPy Simulated Image'
    nda['compressedSize'] = nx*ny
    nda['uncompressedSize'] = nx*ny
    nda['timeStamp'] = time_stamp
    nda['dataTimeStamp'] = time_stamp
    attrs = [pva.NtAttribute('ColorMode', pva.PvInt(color_mode))]
    nda['attribute'] = attrs
    nda['value'] = {'ubyteValue' : image}
    # nda.set(extra_fields_PV_object)
    return nda
