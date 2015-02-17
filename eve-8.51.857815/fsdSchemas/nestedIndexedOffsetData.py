#Embedded file name: F:\depot\streams\olafurth_olafurth-pc_STABLE_2754\fsdSchemas\nestedIndexedOffsetData.py
import logging
log = logging.getLogger(__name__)
import time
import itertools

class NestedKeyDuplicationError(Exception):

    def __init__(self, indexedDuplicateData):
        self.indexedDuplicateData = indexedDuplicateData

    def __str__(self):
        message = ''
        for nestedIndexId, duplicateData in self.indexedDuplicateData.iteritems():
            message += 'Duplicate keys found for index %d:\n' % nestedIndexId
            for key, duplicates in duplicateData.iteritems():
                message += '%s - defined in %s\n' % (str(key), [ x for x in duplicates ])

        return message[:-1]


class IndexedOffsetData(object):

    def __init__(self, offset = 0):
        self.offset = offset
        self.offsetData = {}
        self.nestedIndexedOffsetDataList = []

    def AddOffset(self, additionalOffset):
        self.offset += additionalOffset

    def AddKeyOffsetSizeAndPathToNestedIndexId(self, dataKey, offset, size, path, nestedIndexId):
        if nestedIndexId not in self.offsetData:
            self.offsetData[nestedIndexId] = []
        indexedOffsetData = self.offsetData[nestedIndexId]
        indexedOffsetData.append(_GenerateTupleForOffsetData(dataKey, offset, size, path))

    def Flatten(self):
        log.info('Starting to flatten')
        startTime = time.time()
        flattenedData = _FlattenOffsetData(self)
        t = time.time()
        for nestedIndexId, flattenedDataset in flattenedData.iteritems():
            flattenedData[nestedIndexId] = sorted(flattenedDataset, key=lambda x: x[0])

        log.info('Sorting flattened dict took: %.10f s' % (time.time() - t))
        t = time.time()
        indexedDuplicateData = _GetDuplicateData(flattenedData)
        if len(indexedDuplicateData) > 0:
            raise NestedKeyDuplicationError(indexedDuplicateData)
        log.info('Sorting and checking for duplicates took %.10f' % float(time.time() - t))
        log.info('Flattening, sorting and checking for duplicates took : %f s' % (time.time() - startTime))
        return flattenedData

    def AddNestedIndexedOffsetData(self, nestedIndexedOffsetData):
        self.nestedIndexedOffsetDataList.append(nestedIndexedOffsetData)

    def isEmpty(self):
        return len(self.offsetData) == 0 and len(self.nestedIndexedOffsetDataList) == 0


def _GenerateTupleForOffsetData(dataKey, offset, size, path):
    return (dataKey,
     offset,
     size,
     path)


def _GetKeyFromOffsetData(offsetDataTuple):
    return offsetDataTuple[0]


def _GetPathFromOffsetData(offsetDataTuple):
    return offsetDataTuple[3]


def _AddDataWithAddedOffsetToFlattenedDict(data, additionalOffset, flattenedDataDict):
    for nestedIndexId, offsetData in data.iteritems():
        if nestedIndexId not in flattenedDataDict:
            flattenedDataDict[nestedIndexId] = []
        for key, offset, size, path in offsetData:
            updatedOffsetData = _GenerateTupleForOffsetData(key, offset + additionalOffset, size, path)
            flattenedDataDict[nestedIndexId].append(updatedOffsetData)


def _AddOffsetToNestedIndexedDataList(nestedIndexedOffsetDataList, offset):
    for nestedIndexedOffsetData in nestedIndexedOffsetDataList:
        nestedIndexedOffsetData.AddOffset(offset)


def _FindDuplicateKeysWithPathInList(dataGroupedByKeys):
    duplicateKeysWithPath = {}
    for k, v in dataGroupedByKeys:
        l = list(v)
        if len(l) > 1:
            duplicateKeysWithPath[k] = [ _GetPathFromOffsetData(offsetData) for offsetData in l ]

    return duplicateKeysWithPath


def _GetDuplicateData(flattenedData):
    indexedDuplicateData = {}
    for nestedIndexId, indexedFlattenedData in flattenedData.iteritems():
        d = _FindDuplicateKeysWithPathInList(itertools.groupby(indexedFlattenedData, key=lambda x: _GetKeyFromOffsetData(x)))
        if len(d) > 0:
            indexedDuplicateData[nestedIndexId] = d

    return indexedDuplicateData


def _FlattenOffsetData(indexedOffsetDataObject):
    flattenedDict = {}
    dataStack = [indexedOffsetDataObject]
    startTime = time.time()
    while len(dataStack) != 0:
        data = dataStack.pop()
        if len(data.offsetData) != 0:
            _AddDataWithAddedOffsetToFlattenedDict(data.offsetData, data.offset, flattenedDict)
        if len(data.nestedIndexedOffsetDataList) != 0:
            _AddOffsetToNestedIndexedDataList(data.nestedIndexedOffsetDataList, data.offset)
            dataStack.extend(data.nestedIndexedOffsetDataList)

    log.info('Flattening dict took: %f s' % (time.time() - startTime))
    return flattenedDict
