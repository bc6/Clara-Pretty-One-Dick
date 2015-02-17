#Embedded file name: trinutils\bluestructurelist.py
"""
Contains a wrapper for BlueStructureList that allows accessing list
item elements by name.
"""
import collections
DT_INT8 = 0
DT_INT16 = 1
DT_INT32 = 2
DT_FLOAT16 = 3
DT_FLOAT32 = 4
DT_SHAREDSTRING = 5
DT_FLOAT32x4 = 6
DT_BOOL8 = 7
DT_TYPE_MASK = 7
DT_UNSIGNED_BIT = 8
DT_SIZE_OFFSET = 5
DT_SIZE_MASK = 3 << DT_SIZE_OFFSET

def get_definition_element_type(element):
    """Returns base type constant for structure list definition element"""
    return element[1] & DT_TYPE_MASK


def get_definition_element_size(element):
    """Returns base type size (number of elements in the tuple) for structure list definition element"""
    return ((element[1] & DT_SIZE_MASK) >> DT_SIZE_OFFSET) + 1


class wrap(object):
    """
    Wraps structure list in an object that uses namedtuple istead of
    a tuple to represent elements in the list.
    """

    def __init__(self, structureList):
        self.structureList = structureList
        fieldNames = [ x[0] for x in structureList.GetStructureDefinition() ]
        if len(structureList.GetStructureDefinition()) > 1:
            self.namedtuple = collections.namedtuple(self._get_item_type_name(), fieldNames)
        else:
            self.namedtuple = None

    def _get_item_type_name(self):
        typeName = 'StructureList_'
        for element in self.structureList.GetStructureDefinition():
            typeName += '_'
            if element[1] & DT_UNSIGNED_BIT != 0:
                typeName += 'u'
            t = get_definition_element_type(element)
            if t == DT_INT8:
                typeName += 'int8_'
            elif t == DT_INT16:
                typeName += 'int16_'
            elif t == DT_INT32:
                typeName += 'int32_'
            elif t == DT_FLOAT16:
                typeName += 'float16_'
            elif t == DT_FLOAT32:
                typeName += 'float32_'
            elif t == DT_SHAREDSTRING:
                typeName += 'string_'
            elif t == DT_FLOAT32x4:
                typeName += 'float32x4_'
            elif t == DT_BOOL8:
                typeName += 'bool8_'
            else:
                typeName += 'unknown_'
            typeName += '%s' % get_definition_element_size(element)

        return typeName

    def __len__(self):
        return len(self.structureList)

    def __iter__(self):
        for i in self.structureList:
            if self.namedtuple is None:
                yield i
            else:
                yield self.namedtuple(*i)

    def __getitem__(self, key):
        if self.namedtuple is None:
            return self.structureList[key]
        else:
            return self.namedtuple(*self.structureList[key])

    def __delitem__(self, key):
        if isinstance(key, slice):
            indices = sorted(xrange(*key.indices(len(self.structureList))), reverse=True)
            for i in indices:
                self.structureList.removeAt(i)

        else:
            self.structureList.removeAt(key)

    def clear(self):
        self.structureList.clear()

    def append(self, item):
        if self.namedtuple is None:
            self.structureList.append(item)
        else:
            self.structureList.append(tuple(item))

    def create_item(self, **kwargs):
        """Creates a new item compatible with the structure list. Fills members with
        specified keyword arguments or default values."""
        elements = self.structureList.GetStructureDefinition()
        newItem = []
        for e in elements:
            if e[0] in kwargs:
                newItem.append(kwargs[e[0]])
            else:
                t = get_definition_element_type(e)
                if t == DT_SHAREDSTRING:
                    val = ''
                elif t == DT_FLOAT32x4:
                    val = (0, 0, 0, 0)
                elif t == DT_BOOL8:
                    val = False
                else:
                    val = 0
                size = get_definition_element_size(e)
                if size == 1:
                    newItem.append(val)
                else:
                    newItem.append((val,) * size)

        if self.namedtuple is None:
            return newItem[0]
        else:
            return self.namedtuple(*newItem)
