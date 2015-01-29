#Embedded file name: F:\depot\streams\olafurth_olafurth-pc_STABLE_2754\fsdSchemas\loaders\listLoader.py
import ctypes
import collections
from fsdSchemas.path import FsdDataPathObject
import fsdSchemas.predefinedStructTypes as structTypes

class FixedSizeListIterator(object):

    def __init__(self, data, offset, itemSchema, itemCount, path, itemSize, extraState):
        self.data = data
        self.offset = offset
        self.itemSchema = itemSchema
        self.count = itemCount
        self.itemSize = itemSize
        self.index = -1
        self.__path__ = path
        self.__extraState__ = extraState

    def __iter__(self):
        return self

    def next(self):
        self.index += 1
        if self.index == self.count:
            raise StopIteration()
        return self.__extraState__.RepresentSchemaNode(self.data, self.offset + self.itemSize * self.index, FsdDataPathObject('[%s]' % str(self.index), parent=self.__path__), self.itemSchema)


class FixedSizeListRepresentation(object):

    def __init__(self, data, offset, itemSchema, path, extraState, knownLength = None):
        self.data = data
        self.offset = offset
        self.itemSchema = itemSchema
        self.__extraState__ = extraState
        self.__path__ = path
        if knownLength is None:
            self.count = structTypes.uint32.unpack_from(data, offset)[0]
            self.fixedLength = False
        else:
            self.count = knownLength
            self.fixedLength = True
        self.itemSize = itemSchema['size']

    def __iter__(self):
        countOffset = 0 if self.fixedLength else 4
        return FixedSizeListIterator(self.data, self.offset + countOffset, self.itemSchema, self.count, self.__path__, self.itemSize, self.__extraState__)

    def __len__(self):
        return self.count

    def __getitem__(self, key):
        if type(key) not in (int, long):
            raise TypeError('Invalid key type')
        if key < 0 or key >= self.count:
            raise IndexError('Invalid item index %i for list of length %i' % (key, self.count))
        countOffset = 0 if self.fixedLength else 4
        totalOffset = self.offset + countOffset + self.itemSize * key
        return self.__extraState__.RepresentSchemaNode(self.data, totalOffset, FsdDataPathObject('[%s]' % str(key), parent=self.__path__), self.itemSchema)


class VariableSizedListRepresentation(object):

    def __init__(self, data, offset, itemSchema, path, extraState, knownLength = None):
        self.data = data
        self.offset = offset
        self.itemSchema = itemSchema
        self.__extraState__ = extraState
        self.__path__ = path
        if knownLength is None:
            self.count = structTypes.uint32.unpack_from(data, offset)[0]
            self.fixedLength = False
        else:
            self.count = knownLength
            self.fixedLength = True

    def __len__(self):
        return self.count

    def __getitem__(self, key):
        if type(key) not in (int, long):
            raise TypeError('Invalid key type')
        if key < 0 or key >= self.count:
            raise IndexError('Invalid item index %i for list of length %i' % (key, self.count))
        countOffset = 0 if self.fixedLength else 4
        dataOffsetFromObjectStart = structTypes.uint32.unpack_from(self.data, self.offset + countOffset + 4 * key)[0]
        return self.__extraState__.RepresentSchemaNode(self.data, self.offset + dataOffsetFromObjectStart, FsdDataPathObject('[%s]' % str(key), parent=self.__path__), self.itemSchema)


def ListFromBinaryString(data, offset, schema, path, extraState, knownLength = None):
    knownLength = schema.get('length', knownLength)
    if 'fixedItemSize' in schema:
        listLikeObject = FixedSizeListRepresentation(data, offset, schema['itemTypes'], path, extraState, knownLength)
    else:
        listLikeObject = VariableSizedListRepresentation(data, offset, schema['itemTypes'], path, extraState, knownLength)
    return list(listLikeObject)
