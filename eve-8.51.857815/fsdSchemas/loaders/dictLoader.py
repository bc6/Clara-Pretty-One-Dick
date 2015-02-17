#Embedded file name: F:\depot\streams\olafurth_olafurth-pc_STABLE_2754\fsdSchemas\loaders\dictLoader.py
import ctypes
import collections
from fsdSchemas.path import FsdDataPathObject
import logging
from fsdSchemas.loaders import readBinaryDataFromFileAtOffset, readIntFromBinaryStringAtOffset, readIntFromFileAtOffset
import fsdSchemas.predefinedStructTypes as structTypes
log = logging.getLogger(__name__)
try:
    import pyFSD
    hasPyFSD = True
except ImportError:
    log.error('Could not import pyFSD, falling back to slower python implementation!')
    hasPyFSD = False

def CreatePythonDictOffset(schema, binaryFooterData, path, extraState):
    useOptimizedPythonOffsetStructure = schema['keyTypes']['type'] == 'int'
    buff = ctypes.create_string_buffer(binaryFooterData, len(binaryFooterData))
    if useOptimizedPythonOffsetStructure:
        return StandardFSDOptimizedDictFooter(buff, schema)
    else:
        return StandardFSDDictFooter(buff, 0, schema['keyFooter'], FsdDataPathObject('<keyFooter>', parent=path), extraState)


def CreateDictFooter(schema, binaryFooterData, path, extraState):
    keyType = schema['keyTypes']['type']
    if hasPyFSD and keyType == 'int':
        keyMap = pyFSD.FsdUnsignedIntegerKeyMap()
        keyMap.Initialize(binaryFooterData)
        return CppFsdIntegerKeyMapWrapper(keyMap)
    else:
        return CreatePythonDictOffset(schema, binaryFooterData, path, extraState)


class StandardFSDOptimizedDictFooter(object):

    def __init__(self, data, schema):
        self.data = data
        if 'size' in schema['keyFooter']['itemTypes']['attributes']:
            self.unpacker = structTypes.keyedOffsetDataWithSize
            self.offsetDataHasSizeAttribute = True
        else:
            self.unpacker = structTypes.keyedOffsetData
            self.offsetDataHasSizeAttribute = False
        self.listItemSize = self.unpacker.size
        self.startingOffset = 4
        self.size = readIntFromBinaryStringAtOffset(data, 0)

    def Get(self, key):
        minIndex = 0
        maxIndex = self.size - 1
        while 1:
            if maxIndex < minIndex:
                return None
            meanIndex = (minIndex + maxIndex) / 2
            currentObjectOffset = meanIndex * self.listItemSize + self.startingOffset
            currentKey, offset, size = self.__unpackFromOffset__(currentObjectOffset)
            if currentKey < key:
                minIndex = meanIndex + 1
            elif currentKey > key:
                maxIndex = meanIndex - 1
            else:
                return (offset, size)

    def __len__(self):
        return self.size

    def __unpackFromOffset__(self, currentObjectOffset):
        if self.offsetDataHasSizeAttribute:
            currentKey, offset, size = self.unpacker.unpack_from(self.data, currentObjectOffset)
        else:
            currentKey, offset = self.unpacker.unpack_from(self.data, currentObjectOffset)
            size = 0
        return (currentKey, offset, size)

    def iteritems(self):
        for i in range(0, self.size):
            currentObjectOffset = i * self.listItemSize + self.startingOffset
            currentKey, offset, size = self.__unpackFromOffset__(currentObjectOffset)
            yield (currentKey, (offset, size))


class StandardFSDDictFooter(object):

    def __init__(self, data, offset, schema, path, extraState):
        self.footerData = extraState.factories['list'](data, offset, schema, path, extraState)
        self.size = len(self.footerData)

    def Get(self, key):
        minIndex = 0
        maxIndex = self.size - 1
        while 1:
            if maxIndex < minIndex:
                return None
            meanIndex = (minIndex + maxIndex) / 2
            item = self.footerData[meanIndex]
            if item['key'] < key:
                minIndex = meanIndex + 1
            elif item['key'] > key:
                maxIndex = meanIndex - 1
            else:
                return (item['offset'], getattr(item, 'size', 0))

    def __len__(self):
        return self.size

    def iteritems(self):
        for item in self.footerData:
            yield (item.key, (item.offset, getattr(item, 'size', 0)))


class CppFsdIntegerKeyMapWrapper(object):

    def __init__(self, keyMapObject):
        self.keyMapObject = keyMapObject

    def Get(self, key):
        try:
            return self.keyMapObject.Get(key)
        except IndexError:
            return None

    def __len__(self):
        return self.keyMapObject.length()

    def iteritems(self):
        i = self.keyMapObject.iteritems()
        while True:
            yield i.next()


class DictLoader(object):

    def __init__(self, data, offset, schema, path, extraState):
        self.data = data
        self.offset = offset
        self.schema = schema
        self.sizeOfData = readIntFromBinaryStringAtOffset(self.data, self.offset)
        offsetToSizeOfFooter = self.offset + 4 + self.sizeOfData - 4
        self.sizeOfFooter = readIntFromBinaryStringAtOffset(self.data, offsetToSizeOfFooter)
        self.__extraState__ = extraState
        self.__path__ = path
        self.index = {}
        offsetToStartOfFooter = self.offset + self.sizeOfData - self.sizeOfFooter
        footerData = data[offsetToStartOfFooter:offsetToStartOfFooter + self.sizeOfFooter]
        self.footer = CreatePythonDictOffset(schema, footerData, path, extraState)

    def __getitem__(self, key):
        v = self._Search(key)
        if v is None:
            raise KeyError('key (%s) not found in %s' % (str(key), self.__path__))
        return self.__GetItemFromOffset__(key, v[0])

    def __GetItemFromOffset__(self, key, offset):
        return self.__extraState__.RepresentSchemaNode(self.data, self.offset + 4 + offset, FsdDataPathObject('[%s]' % str(key), parent=self.__path__), self.schema['valueTypes'])

    def __len__(self):
        return len(self.footer)

    def __contains__(self, item):
        try:
            x = self._Search(item)
            return x is not None
        except TypeError:
            return False

    def _Search(self, key):
        if key not in self.index:
            searchResult = self.footer.Get(key)
            if searchResult is not None:
                self.index[key] = searchResult
            else:
                self.index[key] = None
            return searchResult
        return self.index[key]

    def Get(self, key):
        return self.__getitem__(key)

    def get(self, key, default):
        v = self._Search(key)
        if v is not None:
            return self.__GetItemFromOffset__(key, v[0])
        else:
            return default

    def GetIfExists(self, key):
        return self.get(key, None)

    def itervalues(self):
        for key, (offset, size) in self.footer:
            yield self.__GetItemFromOffset__(key, offset)

    def iterkeys(self):
        for key, _ in self.footer.iteritems():
            yield key

    def keys(self):
        return [ k for k, _ in self.footer.iteritems() ]

    def iteritems(self):
        for key, (offset, size) in self.footer.iteritems():
            yield (key, self.__GetItemFromOffset__(key, offset))

    def __iter__(self):
        for i in self.iterkeys():
            yield i


class IndexLoader(object):

    def __init__(self, fileObject, cacheSize, schema, path, extraState, offsetToData = 0, offsetToFooter = 0):
        self.fileObject = fileObject
        self.cacheSize = cacheSize
        self.schema = schema
        self.offsetToFooter = offsetToFooter
        self.offsetToData = offsetToData
        self.__extraState__ = extraState
        self.__path__ = path
        self.fileObjectSize = readIntFromFileAtOffset(self.fileObject, offsetToData)
        self.index = {}
        offsetToFooterSize = self.offsetToData + self.fileObjectSize
        if self.offsetToFooter != 0:
            offsetToFooterSize = self.offsetToFooter - 4
        self.footerDataSize = readIntFromFileAtOffset(self.fileObject, offsetToFooterSize)
        log.info('Loading FSD index for %s. %s', self.__path__, self.__extraState__.FormatSize(self.footerDataSize))
        offsetToStartOfFooterData = offsetToFooterSize - self.footerDataSize
        binaryDictFooter = readBinaryDataFromFileAtOffset(self.fileObject, offsetToStartOfFooterData, self.footerDataSize)
        self.footerData = CreateDictFooter(self.schema, binaryDictFooter, self.__path__, self.__extraState__)
        self.cachedLoadedObjects = collections.OrderedDict()
        self.isSubObjectAnIndex = self.schema['valueTypes'].get('buildIndex', False)
        self.isSubObjectAnIndex &= self.schema['valueTypes']['type'] == 'dict'

    def iterkeys(self):
        for key, _ in self.footerData.iteritems():
            yield key

    def iteritems(self):
        for key, (offset, size) in self.footerData.iteritems():
            yield (key, self.__GetItemFromOffsetAndSize__(key, offset, size))

    def _Search(self, key):
        if key not in self.index:
            searchResult = self.footerData.Get(key)
            if searchResult is not None:
                self.index[key] = searchResult
            else:
                self.index[key] = None
            return searchResult
        else:
            return self.index[key]

    def __getitem__(self, key):
        if key in self.cachedLoadedObjects:
            v = self.cachedLoadedObjects[key]
            del self.cachedLoadedObjects[key]
            self.cachedLoadedObjects[key] = v
            return v
        try:
            dataInfo = self._Search(key)
        except TypeError:
            raise KeyError('Key (%s) not found in %s' % (str(key), self.__path__))

        if dataInfo is None:
            raise KeyError('Key (%s) not found in %s' % (str(key), self.__path__))
        itemOffset, itemSize = dataInfo
        if len(self.cachedLoadedObjects) > self.cacheSize:
            self.cachedLoadedObjects.popitem(last=False)
        item = self.__GetItemFromOffsetAndSize__(key, itemOffset, itemSize)
        self.cachedLoadedObjects[key] = item
        return item

    def __GetItemFromOffsetAndSize__(self, key, itemOffset, itemSize):
        newOffset = 4 + self.offsetToData + itemOffset
        valueSchema = self.schema['valueTypes']
        if valueSchema.get('buildIndex', False):
            v = IndexLoader(self.fileObject, self.cacheSize, valueSchema, FsdDataPathObject('[%s]' % str(key), parent=self.__path__), self.__extraState__, offsetToData=newOffset, offsetToFooter=newOffset + itemSize)
            return v
        else:
            itemData = readBinaryDataFromFileAtOffset(self.fileObject, newOffset, itemSize)
            dataAsBuffer = ctypes.create_string_buffer(itemData, len(itemData))
            v = self.__extraState__.RepresentSchemaNode(dataAsBuffer, 0, FsdDataPathObject('[%s]' % str(key), parent=self.__path__), valueSchema)
            return v

    def __contains__(self, item):
        try:
            return self._Search(item) is not None
        except TypeError:
            return False

    def __len__(self):
        return len(self.footerData)

    def Get(self, key):
        return self.__getitem__(key)

    def GetIfExists(self, key):
        return self.get(key, None)

    def get(self, key, default):
        try:
            return self.__getitem__(key)
        except (KeyError, IndexError):
            return default


class SubIndexLoader(object):

    def __init__(self, indexedOffsetTable, indexedSchemas, offsetToData, fileObject, extraState, path):
        self.fileObject = fileObject
        self.indexedOffsetTable = indexedOffsetTable
        self.indexedSchemas = indexedSchemas
        self.offsetToData = offsetToData
        self.__extraState__ = extraState
        self.__path__ = path

    def iterkeys(self):
        for offsetTable in self.indexedOffsetTable.values():
            for key, value in offsetTable.iteritems():
                yield key

    def iteritems(self):
        for nestedIndexId, offsetTable in self.indexedOffsetTable.iteritems():
            for key, value in offsetTable.iteritems():
                yield (key, self.__getValueForKeyInIndex__(key, nestedIndexId))

    def __getValueForKeyInIndex__(self, key, nestedIndex):
        try:
            offsetData = self.indexedOffsetTable[nestedIndex].Get(key)
        except TypeError:
            raise KeyError('Key (%s) not found in %s' % (str(key), self.__path__))

        if offsetData is None:
            raise KeyError('Key (%s) not found in %s' % (str(key), self.__path__))
        offset = offsetData[0]
        size = offsetData[1]
        valueSchema = self.indexedSchemas[nestedIndex]['valueTypes']
        offsetToStartOfData = 4 + offset + self.offsetToData
        if valueSchema.get('buildIndex', False):
            v = IndexLoader(self.fileObject, 100, valueSchema, FsdDataPathObject('[%s]' % str(key), parent=self.__path__), self.__extraState__, offsetToData=offsetToStartOfData, offsetToFooter=offsetToStartOfData + size)
            return v
        else:
            itemData = readBinaryDataFromFileAtOffset(self.fileObject, offsetToStartOfData, size)
            dataAsBuffer = ctypes.create_string_buffer(itemData, len(itemData))
            v = self.__extraState__.RepresentSchemaNode(dataAsBuffer, 0, FsdDataPathObject('[%s]' % str(key), parent=self.__path__), valueSchema)
            return v

    def __getitem__(self, key):
        for nestedIndexId in self.indexedOffsetTable:
            try:
                return self.__getValueForKeyInIndex__(key, nestedIndexId)
            except KeyError:
                pass

        raise KeyError('Key (%s) not found in %s' % (str(key), self.__path__))

    def __contains__(self, item):
        try:
            self.__getitem__(item)
        except KeyError:
            return False

        return True

    def __len__(self):
        sum = 0
        for offsetTable in self.indexedOffsetTable.values():
            sum += len(offsetTable)

        return sum

    def Get(self, key):
        return self.__getitem__(key)

    def GetIfExists(self, key):
        return self.get(key, None)

    def get(self, key, default):
        try:
            return self.__getitem__(key)
        except (KeyError, IndexError):
            return default


class MultiIndexLoader(IndexLoader):

    def __init__(self, fileObject, cacheSize, schema, path, extraState, offsetToData = 0):
        IndexLoader.__init__(self, fileObject, cacheSize, schema, path, extraState, offsetToData=offsetToData)
        offsetToAttributeLookupTableSize = self.offsetToData + 4 + self.fileObjectSize - 4 - self.footerDataSize - 4
        self.attributeLookupTableSize = readIntFromFileAtOffset(self.fileObject, offsetToAttributeLookupTableSize)
        startOfAttributeLookupTable = offsetToAttributeLookupTableSize - self.attributeLookupTableSize
        attributeLookupTable = readBinaryDataFromFileAtOffset(self.fileObject, startOfAttributeLookupTable, self.attributeLookupTableSize)
        attributeLookupTable = ctypes.create_string_buffer(attributeLookupTable, len(attributeLookupTable))
        self.nestedIndexIdToOffsetTable = self.__extraState__.RepresentSchemaNode(attributeLookupTable, 0, FsdDataPathObject('<MultiIndexAttributes>', parent=self.__path__), self.schema['subIndexOffsetLookup'])
        log.info('Attribute lookup table for MultiIndex %s. %s', self.__path__, self.__extraState__.FormatSize(len(attributeLookupTable)))
        self.attributeCache = {}
        nestedIndexIdToOffsetData = {}
        combinedNestedOffsetDataSize = 0
        for index, offsetAndSizeOfOffsetData in self.nestedIndexIdToOffsetTable.iteritems():
            offsetToNestedDictionaryOffsetData = offsetToData + offsetAndSizeOfOffsetData.offset
            binaryNestedDictionaryOffsetData = readBinaryDataFromFileAtOffset(self.fileObject, offsetToNestedDictionaryOffsetData, offsetAndSizeOfOffsetData.size)
            combinedNestedOffsetDataSize += len(binaryNestedDictionaryOffsetData)
            nestedIndexIdToOffsetData[index] = CreateDictFooter(self.schema['indexableSchemas'][index], binaryNestedDictionaryOffsetData, FsdDataPathObject('<MultiIndexAttributes>.footer[%i]' % index, parent=self.__path__), self.__extraState__)

        log.info('Total size of nested offset data kept in memory %s. %s' % (self.__path__, self.__extraState__.FormatSize(combinedNestedOffsetDataSize)))
        for indexName, indices in self.schema['indexNameToIds'].iteritems():
            indexToDictOffsetTable = {}
            indexToSchema = {}
            for index in indices:
                indexToDictOffsetTable[index] = nestedIndexIdToOffsetData[index]
                indexToSchema[index] = self.schema['indexableSchemas'][index]

            self.attributeCache[indexName] = SubIndexLoader(indexToDictOffsetTable, indexToSchema, offsetToData, self.fileObject, self.__extraState__, FsdDataPathObject('<MultiIndexAttributes>.%s' % indexName, parent=self.__path__))

    def __getattr__(self, name):
        if name in self.attributeCache:
            return self.attributeCache[name]
        raise AttributeError("MultiIndex Dictionary does not contain attribute '" + name + "'")
