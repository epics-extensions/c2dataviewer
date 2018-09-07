# -*- coding: utf-8 -*-

from collections import OrderedDict
from pvaccess import Channel

class PvUtility:

    @classmethod
    def addDataArray(cls, groupSize, groupCounter):
        """

        :param groupSize:
        :param groupCounter:
        :return:
        """
        depth = len(groupCounter)
        gc = groupCounter[depth - 1] + 1
        if gc > groupSize:
            gc = 1
            for d in range(depth - 2, -1, -1):
                gc2 = groupCounter[d] + 1
                if gc2 <= groupSize:
                    groupCounter[d] = gc2
                    break
                gc2 = 1
                groupCounter[d] = gc2
        groupCounter[depth - 1] = gc
        return groupCounter

    @classmethod
    def createDataArrayDict(cls, name, groupSize):
        """

        :param name: EPICS PV name
        :param groupSize:
        :return:
        """
        channel = Channel(name)

        dataArrays = []
        pv = channel.get('')
        sDict = pv.getStructureDict()
        for (key, value) in sDict.items():
            if type(value) == list:  # Make type comparison compatible with PY2 & PY3
                # if type(value) == types.ListType:

                dataArrays.append(key)
        dataArrays.sort()
        # print('There are %s data arrays for PV %s' % (len(dataArrays), pvName))

        depth = 0
        maxDataArrays = 1
        nDataArrays = len(dataArrays)
        while True:
            depth += 1
            maxDataArrays *= groupSize
            if maxDataArrays >= nDataArrays:
                break

        dataArrayDict = OrderedDict()
        dataArrayDict.lastChild = None
        dataArrayDict.firstIndex = 1
        groupCounter = [1] * depth
        groupCounter[-1] = 0
        dataArrayIndex = 0

        for a in dataArrays:
            dataArrayIndex += 1
            groupCounter = cls.addDataArray(groupSize, groupCounter)
            # print('Channel: %s, Group Counter: %s' % (a, groupCounter))
            aDict = dataArrayDict
            for d in range(0, depth - 1):
                aDict.lastIndex = dataArrayIndex
                aDict.title = 'Fields %s-%s' % (aDict.firstIndex, aDict.lastIndex)
                # print('Title: %s' % (aDict.title))
                key = groupCounter[d]
                if key not in aDict.keys():
                    aDict2 = OrderedDict()
                    aDict2.parent = aDict
                    aDict2.firstIndex = dataArrayIndex
                    aDict2.lastChild = None
                    if aDict.lastChild:
                        aDict.lastChild.lastIndex = dataArrayIndex - 1
                        # print('Depth: %d, %s-%s' % (d+1, aDict.lastChild.firstIndex, aDict.lastChild.lastIndex))
                        aDict.lastChild.title = 'Fields %s-%s' % (aDict.lastChild.firstIndex, aDict.lastChild.lastIndex)
                    aDict.lastChild = aDict2
                    aDict[key] = aDict2
                else:
                    aDict2 = aDict.get(key)
                aDict = aDict2
            key = groupCounter[depth - 1]
            # Form array groups as tuples of (label,field)
            aDict[key] = (a, a)
            aDict.lastIndex = dataArrayIndex
            aDict.title = 'Fields %s-%s' % (aDict.firstIndex, aDict.lastIndex)

        return dataArrayDict

    @classmethod
    def printGroups(cls, dataArrayDict, depth=0):
        """

        :param dataArrayDict:
        :param depth:
        :return:
        """
        for key in dataArrayDict.keys():
            if type(dataArrayDict[key]) == tuple:  # Make type comparison compatible with PY2 & PY3
                # if type(dataArrayDict[key]) == types.TupleType:
                fieldLabel, fieldName = dataArrayDict[key]
                print('%s%s %s (%s)' % (' ' * depth, key, fieldLabel, fieldName))
            else:
                print('%s%s' % (' ' * depth, dataArrayDict[key].title))
                cls.printGroups(dataArrayDict[key], depth + 1)


#############################################################################
#
if __name__ == '__main__':
    pvName = 'fbc_monitor_data'
    groupSize = 9
    aDict = PvUtility.createDataArrayDict(pvName, groupSize)
    PvUtility.printGroups(aDict)

